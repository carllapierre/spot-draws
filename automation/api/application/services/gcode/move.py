import time
import traceback

from bosdyn import geometry
from bosdyn.api import basic_command_pb2, geometry_pb2, trajectory_pb2
from bosdyn.api.spot import robot_command_pb2
from bosdyn.client import robot_command
from bosdyn.client.frame_helpers import ODOM_FRAME_NAME

# TODO: ISSUE #145 Replace with config
NAV_VELOCITY_MAX_YAW = 1.2  # rad/s
NAV_VELOCITY_MAX_X = 1.0  # m/s
NAV_VELOCITY_MAX_Y = 0.5  # m/s
VELOCITY_CMD_DURATION = 6


def block_for_trajectory_cmd(
    command_client, cmd_id, timeout_sec=None, logger=None
) -> bool:
    """
    Helper that blocks until a trajectory command reaches STATUS_AT_GOAL or a timeout is
    exceeded.
    Args:
        command_client: robot command client, used to request feedback
        cmd_id: command ID returned by the robot when the trajectory command was sent
        timeout_sec: optional number of seconds after which we'll return no matter what
            the robot's state is.
    Return values:
        True if reaches STATUS_AT_GOAL, False otherwise.
    """
    success = False
    try:
        start_time = time.time()

        if timeout_sec is not None:
            end_time = start_time + timeout_sec
            now = time.time()

        while timeout_sec is None or now < end_time:
            feedback_resp = command_client.robot_command_feedback(cmd_id)

            current_state = (
                feedback_resp.feedback.mobility_feedback.se2_trajectory_feedback.status
            )

            if (
                current_state
                == basic_command_pb2.SE2TrajectoryCommand.Feedback.STATUS_AT_GOAL
            ):
                success = True

            time.sleep(0.1)
            now = time.time()

    except Exception as exc:
        if (logger is not None):
            logger.error(
                "An exception occurred while running block_for_trajectory_cmd. "
                + "Exception was: %s. Traceback was: %s" %
                exc,
                traceback.format_exc(),
            )

    return success


def get_default_body_control() -> robot_command_pb2.BodyControlParams:
    """Creates default body control params for current body position"""
    footprint_R_body = geometry.EulerZXY()
    position = geometry_pb2.Vec3(x=0.0, y=0.0, z=0.0)
    rotation = footprint_R_body.to_quaternion()
    pose = geometry_pb2.SE3Pose(position=position, rotation=rotation)
    point = trajectory_pb2.SE3TrajectoryPoint(pose=pose)
    trajectory = trajectory_pb2.SE3Trajectory(points=[point])
    return robot_command_pb2.BodyControlParams(base_offset_rt_footprint=trajectory)


def get_mobility_params(
    x_velocity=NAV_VELOCITY_MAX_X,
    y_velocity=NAV_VELOCITY_MAX_Y,
    yaw_velocity=NAV_VELOCITY_MAX_YAW,
) -> robot_command_pb2.MobilityParams:
    """
    Creates MobilityParams
    """
    speed_limit = geometry_pb2.SE2VelocityLimit(
        max_vel=geometry_pb2.SE2Velocity(
            linear=geometry_pb2.Vec2(x=x_velocity, y=y_velocity),
            angular=yaw_velocity,
        )
    )
    body_control = get_default_body_control()
    mobility_params = robot_command_pb2.MobilityParams(
        vel_limit=speed_limit,
        obstacle_params=None,
        body_control=body_control,
        locomotion_hint=robot_command_pb2.HINT_TROT,
    )
    return mobility_params


def move_command(
    robot,
    command_client,
    d_x=0.0,
    d_y=0.0,
    r_rot=0.0,
    body_height=0.0,
    use_body_frame=True,
    logger=None,
):
    """
    Creates and performs cmd based on inputs
    Args:
        d_x (float): Distance in meters to move spot forward
        d_y (float): Distance in meters to move spot left (slide/strafe)
        r_rot (float): Radian in which to rotate spot left
        body_height (float): Height in meters relative to default
    """
    try:
        # Ensure only one of the following params are set: d_x, d_y, r_rot
        non_default_params = [param for param in (d_x, d_y, r_rot) if param != 0.0]
        if len(non_default_params) > 1:
            raise ValueError("More than one parameter is not set to the default value.")

        if use_body_frame:
            tolerance = 1e-9  # Set a small tolerance value
            if abs(d_x) > tolerance:
                time_to_move_in_seconds = abs(d_x / NAV_VELOCITY_MAX_X)
            elif abs(d_y) > tolerance:
                time_to_move_in_seconds = abs(d_y / NAV_VELOCITY_MAX_Y)
            elif abs(r_rot) > tolerance:
                time_to_move_in_seconds = abs(r_rot / NAV_VELOCITY_MAX_YAW)
            elif abs(body_height) > tolerance:
                time_to_move_in_seconds = 1
            else:
                time_to_move_in_seconds = VELOCITY_CMD_DURATION

            command = robot_command.RobotCommandBuilder.synchro_trajectory_command_in_body_frame(  # noqa: E501
                goal_x_rt_body=d_x,
                goal_y_rt_body=d_y,
                goal_heading_rt_body=r_rot,
                frame_tree_snapshot=robot.get_frame_tree_snapshot(),
                body_height=body_height,
            )
            cmd_id = command_client.robot_command(
                command,
                end_time_secs=time.time() + time_to_move_in_seconds,
            )
        else:
            frame = ODOM_FRAME_NAME
            position = geometry_pb2.Vec2(x=d_x, y=d_y)
            goal_se2 = geometry_pb2.SE2Pose(position=position, angle=d_y)
            cmd = robot_command.RobotCommandBuilder.synchro_se2_trajectory_command(
                goal_se2,
                frame,
                body_height=body_height,
            )
            cmd_id = command_client.robot_command(
                cmd,
                end_time_secs=time.time() + VELOCITY_CMD_DURATION,
            )

        block_for_trajectory_cmd(
            command_client,
            cmd_id,
            timeout_sec=time_to_move_in_seconds + 1,
        )
    except Exception as exc:
        if (logger is not None):
            logger.error(
                "An exception occurred while running move_command. "
                + "Exception was: %s. Traceback was: %s" %
                exc,
                traceback.format_exc(),
            )
        else:
            print('Exception throw in move_command', exc)