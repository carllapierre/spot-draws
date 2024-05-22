import argparse
import configparser
import os
import sys
import time

import numpy as np

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.api import geometry_pb2
from bosdyn.client.arm_surface_contact import ArmSurfaceContactClient
from bosdyn.client.frame_helpers import (
    GRAV_ALIGNED_BODY_FRAME_NAME,
    ODOM_FRAME_NAME,
    VISION_FRAME_NAME,
    get_a_tform_b,
    math_helpers,
)
from bosdyn.client.math_helpers import Quat, SE3Pose, math
from bosdyn.client.robot_command import (
    RobotCommandBuilder,
    RobotCommandClient,
    block_until_arm_arrives,
    blocking_stand,
)
from bosdyn.client.robot_state import RobotStateClient
from application.classes.spot import Spot
from application.exceptions import NoRobotError
from application.services.gcode.gcode_reader import GCodeReader
from application.services.gcode.gcode_helpers import (
    make_orthogonal,
    get_transforms,
    move_arm,
    do_pause,
    resize_gcode_string
)
from application.services.gcode.fiducial import FollowFiducial
from application.services.gcode.move import move_command

script_dir = os.path.dirname(os.path.abspath(__file__))

GENERIC_ERROR_MESSAGE = 'Issue occurred while running the gcode script.'
FOLLOW_FIDUCIAL_OPTIONS = {
    'body_length': 1.1,
    'limit_speed': True, # Limit the robot's walking speed.
    'avoid_obstacles': True,  # Disable obstacle avoidance.
}

START_AT_FIDUCIAL = False
RUN_GCODE = True
RETURN_TO_FIDUCIAL = False

class GCodeService(Spot):
    def __init__(self, requires_spot=True):
        super().__init__()

        if requires_spot is True and self.robot is None:
            raise NoRobotError()

    def run_gcode(self, gcode_src=None, test_file_parsing=True):
        config_path = os.path.join(script_dir, "gcode/gcode.cfg")

        config_parser = configparser.ConfigParser()
        config_parser.read(config_path)

        self.robot.logger.info(f"Sections: {str(config_parser.sections())}")

        gcode_backup = os.path.join(script_dir, "gcode/test/box_hex.gcode")

        gcode_file = os.path.join(script_dir, "gcode/temp.gcode")
        with open(gcode_file, 'w') as f:
            f.write(resize_gcode_string(gcode_src) if gcode_src else open(gcode_backup, 'r').read())

        if self.robot is None:
            return gcode_file

        scale = config_parser.getfloat("General", "scale")
        min_dist_to_goal = config_parser.getfloat("General", "min_dist_to_goal")
        allow_walking = config_parser.getboolean("General", "allow_walking")
        velocity = config_parser.getfloat("General", "velocity")
        press_force_percent = config_parser.getfloat("General", "press_force_percent")
        below_z_is_admittance = config_parser.getfloat(
            "General", "below_z_is_admittance"
        )
        travel_z = config_parser.getfloat("General", "travel_z")
        gcode_start_x = config_parser.getfloat("General", "gcode_start_x")
        gcode_start_y = config_parser.getfloat("General", "gcode_start_y")
        draw_on_wall = config_parser.getboolean("General", "draw_on_wall")
        use_vision_frame = config_parser.getboolean("General", "use_vision_frame")
        use_xy_to_z_cross_term = config_parser.getboolean(
            "General", "use_xy_to_z_cross_term"
        )
        bias_force_x = config_parser.getfloat("General", "bias_force_x")

        if velocity <= 0:
            return f"Velocity must be greater than 0. Currently is: {velocity}"

        if use_vision_frame:
            api_send_frame = VISION_FRAME_NAME
        else:
            api_send_frame = ODOM_FRAME_NAME

        gcode = None

        if test_file_parsing:
            gcode.test_file_parsing()
            return 'Test file parsing complete.'

        self.robot.logger.info(f"Gcode file: {gcode_file}")

        gcode = GCodeReader(
            gcode_file,
            scale,
            self.robot.logger,
            below_z_is_admittance,
            travel_z,
            draw_on_wall,
            gcode_start_x,
            gcode_start_y,
        )

        arm_surface_contact_client = self.robot.ensure_client(
            ArmSurfaceContactClient.default_service_name
        )

        # Only one client at a time can operate a robot. Clients acquire a lease to
        # indicate that they want to control a robot. Acquiring may fail if another
        # client is currently controlling the robot. When the client is done
        # controlling the robot, it should return the lease so other clients can
        # control it. Note that the lease is returned as the "finally" condition in this
        # try-catch-finally block.
        lease_client = self.robot.ensure_client(
            bosdyn.client.lease.LeaseClient.default_service_name
        )
        with bosdyn.client.lease.LeaseKeepAlive(
            lease_client, must_acquire=True, return_at_exit=True
        ):
            # Now, we are ready to power on the robot. This call will block until the power
            # is on. Commands would fail if this did not happen. We can also check that the robot is
            # powered at any point.
            self.robot.logger.info(
                "Powering on robot... This may take a several seconds."
            )
            self.robot.power_on(timeout_sec=20)
            assert self.robot.is_powered_on(), "Robot power on failed."
            self.robot.logger.info("Robot powered on.")

            # Tell the robot to stand up. The command service is used to issue commands to a robot.
            # The set of valid commands for a robot depends on hardware configuration. See
            # RobotCommandBuilder for more detailed examples on command building. The robot
            # command service requires timesync between the robot and the client.
            self.robot.logger.info("Commanding robot to stand...")
            command_client = self.robot.ensure_client(
                RobotCommandClient.default_service_name
            )
            blocking_stand(command_client, timeout_sec=10)
            self.robot.logger.info("Robot standing.")

            if (START_AT_FIDUCIAL):
                fiducial_follower = FollowFiducial(
                        self.robot,
                        FOLLOW_FIDUCIAL_OPTIONS,
                        self.robot.logger,
                        target_fiducial_number=2,
                        distance_margin=0.01,
                    )
                result = fiducial_follower.start()
                if result is None:
                    self.robot.logger.error('Unable to find fiducial at start of gcode program.')

                move_command(self.robot, command_client, d_x=-.1)

            if (RUN_GCODE):
                robot_state_client = self.robot.ensure_client(
                    RobotStateClient.default_service_name
                )
                # Update state
                robot_state = robot_state_client.get_robot_state()

                # Prep arm

                # Build a position to move the arm to (in meters, relative to the body frame's origin)
                x = 0.75
                y = 0

                if not draw_on_wall:
                    z = -0.35

                    qw = 0.707
                    qx = 0
                    qy = 0.707
                    qz = 0
                else:
                    z = -0.25

                    qw = 1
                    qx = 0
                    qy = 0
                    qz = 0

                flat_body_T_hand = math_helpers.SE3Pose(
                    x, y, z, math_helpers.Quat(w=qw, x=qx, y=qy, z=qz)
                )
                odom_T_flat_body = get_a_tform_b(
                    robot_state.kinematic_state.transforms_snapshot,
                    ODOM_FRAME_NAME,
                    GRAV_ALIGNED_BODY_FRAME_NAME,
                )
                odom_T_hand = odom_T_flat_body * flat_body_T_hand

                self.robot.logger.info("Moving arm to starting position.")

                # Send the request
                odom_T_hand_obj = odom_T_hand.to_proto()

                move_time = 0.000001  # move as fast as possible because we will use (default) velocity/accel limiting.

                arm_command = RobotCommandBuilder.arm_pose_command(
                    odom_T_hand_obj.position.x,
                    odom_T_hand_obj.position.y,
                    odom_T_hand_obj.position.z,
                    odom_T_hand_obj.rotation.w,
                    odom_T_hand_obj.rotation.x,
                    odom_T_hand_obj.rotation.y,
                    odom_T_hand_obj.rotation.z,
                    ODOM_FRAME_NAME,
                    move_time,
                )

                command = RobotCommandBuilder.build_synchro_command(arm_command)

                cmd_id = command_client.robot_command(command)

                # Wait for the move to complete
                block_until_arm_arrives(command_client, cmd_id)

                # Update state and Get the hand position
                robot_state = robot_state_client.get_robot_state()
                (world_T_body, _body_T_hand, world_T_hand, _odom_T_body) = get_transforms(
                    use_vision_frame, robot_state
                )

                world_T_admittance_frame = geometry_pb2.SE3Pose(
                    position=geometry_pb2.Vec3(x=0, y=0, z=0),
                    rotation=geometry_pb2.Quaternion(w=1, x=0, y=0, z=0),
                )
                if draw_on_wall:
                    # Create an admittance frame that has Z- along the robot's X axis
                    xhat_ewrt_robot = [0, 0, 1]
                    xhat_ewrt_vo = [0, 0, 0]
                    (xhat_ewrt_vo[0], xhat_ewrt_vo[1], xhat_ewrt_vo[2]) = (
                        world_T_body.rot.transform_point(
                            xhat_ewrt_robot[0], xhat_ewrt_robot[1], xhat_ewrt_robot[2]
                        )
                    )
                    (z1, z2, z3) = world_T_body.rot.transform_point(-1, 0, 0)
                    zhat_temp = [z1, z2, z3]
                    zhat = make_orthogonal(xhat_ewrt_vo, zhat_temp)
                    yhat = np.cross(zhat, xhat_ewrt_vo)
                    mat = np.array([xhat_ewrt_vo, yhat, zhat]).transpose()
                    q_wall = Quat.from_matrix(mat)

                    zero_vec3 = geometry_pb2.Vec3(x=0, y=0, z=0)
                    q_wall_proto = geometry_pb2.Quaternion(
                        w=q_wall.w, x=q_wall.x, y=q_wall.y, z=q_wall.z
                    )

                    world_T_admittance_frame = geometry_pb2.SE3Pose(
                        position=zero_vec3, rotation=q_wall_proto
                    )

                # Touch the ground/wall
                move_arm(
                    robot_state,
                    True,
                    [world_T_hand],
                    arm_surface_contact_client,
                    velocity,
                    allow_walking,
                    world_T_admittance_frame,
                    press_force_percent,
                    api_send_frame,
                    use_xy_to_z_cross_term,
                    bias_force_x,
                )

                time.sleep(1.0)
                (world_T_body, _body_T_hand, world_T_hand, odom_T_body) = get_transforms(
                    use_vision_frame, robot_state
                )

                odom_T_ground_plane = get_a_tform_b(
                    robot_state.kinematic_state.transforms_snapshot, "odom", "gpe"
                )
                world_T_odom = world_T_body * odom_T_body.inverse()

                (gx, gy, gz) = world_T_odom.transform_point(
                    odom_T_ground_plane.x, odom_T_ground_plane.y, odom_T_ground_plane.z
                )
                ground_plane_rt_vo = [gx, gy, gz]

                # Compute the robot's position on the ground plane.
                # ground_plane_T_robot = odom_T_ground_plane.inverse() *

                # Compute an origin.
                if not draw_on_wall:
                    # For on the ground:
                    #   xhat = body x
                    #   zhat = (0,0,1)

                    # Ensure the origin is gravity aligned, otherwise we get some height drift.
                    zhat = [0.0, 0.0, 1.0]
                    (x1, x2, x3) = world_T_body.rot.transform_point(1.0, 0.0, 0.0)
                    xhat_temp = [x1, x2, x3]
                    xhat = make_orthogonal(zhat, xhat_temp)
                    yhat = np.cross(zhat, xhat)
                    mat = np.array([xhat, yhat, zhat]).transpose()
                    vo_Q_origin = Quat.from_matrix(mat)

                    world_T_origin = SE3Pose(
                        world_T_hand.x, world_T_hand.y, world_T_hand.z, vo_Q_origin
                    )
                else:
                    world_T_origin = world_T_hand

                gcode.set_origin(world_T_origin, world_T_admittance_frame)
                self.robot.logger.info("Origin set")

                (is_admittance, world_T_goals, is_pause) = gcode.get_next_world_T_goals(
                    ground_plane_rt_vo
                )

                while is_pause:
                    do_pause()
                    (is_admittance, world_T_goals, is_pause) = gcode.get_next_world_T_goals(
                        ground_plane_rt_vo
                    )

                if world_T_goals is None:
                    # we're done!
                    done = True

                move_arm(
                    robot_state,
                    is_admittance,
                    world_T_goals,
                    arm_surface_contact_client,
                    velocity,
                    allow_walking,
                    world_T_admittance_frame,
                    press_force_percent,
                    api_send_frame,
                    use_xy_to_z_cross_term,
                    bias_force_x,
                )
                odom_T_hand_goal = world_T_odom.inverse() * world_T_goals[-1]
                last_admittance = is_admittance

                done = False
                while not done:

                    # Update state
                    robot_state = robot_state_client.get_robot_state()

                    # Determine if we are at the goal point
                    (world_T_body, body_T_hand, _world_T_hand, odom_T_body) = (
                        get_transforms(use_vision_frame, robot_state)
                    )

                    (gx, gy, gz) = world_T_odom.transform_point(
                        odom_T_ground_plane.x, odom_T_ground_plane.y, odom_T_ground_plane.z
                    )
                    ground_plane_rt_vo = [gx, gy, gz]

                    world_T_odom = world_T_body * odom_T_body.inverse()
                    # odom_T_hand = odom_T_body * body_T_hand

                    admittance_frame_T_world = math_helpers.SE3Pose.from_proto(
                        world_T_admittance_frame
                    ).inverse()
                    admit_frame_T_hand = (
                        admittance_frame_T_world * world_T_odom * odom_T_body * body_T_hand
                    )
                    admit_frame_T_hand_goal = (
                        admittance_frame_T_world * world_T_odom * odom_T_hand_goal
                    )

                    if is_admittance:
                        dist = math.sqrt(
                            (admit_frame_T_hand.x - admit_frame_T_hand_goal.x) ** 2
                            + (admit_frame_T_hand.y - admit_frame_T_hand_goal.y) ** 2
                        )
                        # + (admit_frame_T_hand.z - admit_frame_T_hand_goal.z)**2 )
                    else:
                        dist = math.sqrt(
                            (admit_frame_T_hand.x - admit_frame_T_hand_goal.x) ** 2
                            + (admit_frame_T_hand.y - admit_frame_T_hand_goal.y) ** 2
                            + (admit_frame_T_hand.z - admit_frame_T_hand_goal.z) ** 2
                        )

                    arm_near_goal = dist < min_dist_to_goal

                    if arm_near_goal:
                        # Compute where to go.
                        (is_admittance, world_T_goals, is_pause) = (
                            gcode.get_next_world_T_goals(ground_plane_rt_vo)
                        )

                        while is_pause:
                            do_pause()
                            (is_admittance, world_T_goals, is_pause) = (
                                gcode.get_next_world_T_goals(ground_plane_rt_vo)
                            )

                        if world_T_goals is None:
                            # we're done!
                            done = True
                            self.robot.logger.info("Gcode program finished.")
                            break

                        move_arm(
                            robot_state,
                            is_admittance,
                            world_T_goals,
                            arm_surface_contact_client,
                            velocity,
                            allow_walking,
                            world_T_admittance_frame,
                            press_force_percent,
                            api_send_frame,
                            use_xy_to_z_cross_term,
                            bias_force_x,
                        )
                        odom_T_hand_goal = world_T_odom.inverse() * world_T_goals[-1]

                        if is_admittance != last_admittance:
                            if is_admittance:
                                print("Waiting for touchdown...")
                                time.sleep(1.0)  # pause to wait for touchdown
                            else:
                                time.sleep(1.0)
                        last_admittance = is_admittance
                    elif not is_admittance:
                        # We are in a travel move, so we'll keep updating to account for a changing
                        # ground plane.
                        (is_admittance, _world_T_goals, _is_pause) = (
                            gcode.get_next_world_T_goals(
                                ground_plane_rt_vo, read_new_line=False
                            )
                        )

                # At the end, walk back to the start.
                self.robot.logger.info("Done with gcode, going to stand...")
                blocking_stand(command_client, timeout_sec=10)
                self.robot.logger.info("Robot standing")

            if (RETURN_TO_FIDUCIAL):
                fiducial_follower = FollowFiducial(
                    self.robot,
                    FOLLOW_FIDUCIAL_OPTIONS,
                    self.robot.logger,
                    target_fiducial_number=2,
                    distance_margin=0,
                )
                result = fiducial_follower.start()
                if result is None:
                    self.robot.logger.error('Unable to return to fiducial at end of gcode program.')
                    # return "Unable to return to fiducial at end of gcode program."

            self.robot.logger.info("Done.")

            # Power the robot off. By specifying "cut_immediately=False", a safe power off command
            # is issued to the robot. This will attempt to sit the robot before powering off.
            self.robot.power_off(cut_immediately=False, timeout_sec=20)
            assert not self.robot.is_powered_on(), "Robot power off failed."
            self.robot.logger.info("Robot safely powered off.")

            return "Gcode program finished."


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument(
        "--test-file-parsing",
        action="store_true",
        help="Try parsing the gcode, without executing on a robot",
    )
    options = parser.parse_args()
    try:
        run_gcode(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.exception("Threw an exception")
        return False


if __name__ == "__main__":
    if not main():
        sys.exit(1)
