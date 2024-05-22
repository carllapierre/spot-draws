import numpy as np
from google.protobuf import duration_pb2, wrappers_pb2

from bosdyn.api import (
    arm_surface_contact_pb2,
    arm_surface_contact_service_pb2,
    geometry_pb2,
    trajectory_pb2,
)
from bosdyn.client.frame_helpers import get_a_tform_b
from bosdyn.client.math_helpers import math
from bosdyn.client.robot_command import RobotCommandBuilder


def make_orthogonal(primary, secondary):
    p = primary / np.linalg.norm(primary, ord=2, axis=0, keepdims=True)
    s = secondary / np.linalg.norm(secondary, ord=2, axis=0, keepdims=True)

    u = np.subtract(s, np.multiply(np.dot(p, s) / np.dot(s, s), p))

    normalized_u = u / np.linalg.norm(u, ord=2, axis=0, keepdims=True)
    return normalized_u


def move_along_trajectory(frame, velocity, se3_poses):
    """Builds an ArmSE3PoseCommand the arm to a point at a specific speed.  Builds a
    trajectory from  the current location to a new location
    velocity is in m/s"""

    last_pose = None
    last_t = 0
    points = []

    # Create a trajectory from the points
    for pose in se3_poses:
        if last_pose is None:
            time_in_sec = 0
            seconds = int(0)
            nanos = int(0)
        else:
            # Compute the distance from the current hand position to the new hand position
            dist = math.sqrt(
                (last_pose.x - pose.x) ** 2
                + (last_pose.y - pose.y) ** 2
                + (last_pose.z - pose.z) ** 2
            )
            time_in_sec = dist / velocity
            seconds = int(time_in_sec + last_t)
            nanos = int((time_in_sec + last_t - seconds) * 1e9)

        position = geometry_pb2.Vec3(x=pose.x, y=pose.y, z=pose.z)
        rotation = geometry_pb2.Quaternion(
            w=pose.rot.w, x=pose.rot.x, y=pose.rot.y, z=pose.rot.z
        )
        this_se3_pose = geometry_pb2.SE3Pose(position=position, rotation=rotation)

        points.append(
            trajectory_pb2.SE3TrajectoryPoint(
                pose=this_se3_pose,
                time_since_reference=duration_pb2.Duration(
                    seconds=seconds, nanos=nanos
                ),
            )
        )

        last_pose = pose
        last_t = time_in_sec + last_t

    hand_trajectory = trajectory_pb2.SE3Trajectory(points=points)

    return hand_trajectory


def move_arm(
    robot_state,
    is_admittance,
    world_T_goals,
    arm_surface_contact_client,
    velocity,
    allow_walking,
    world_T_admittance,
    press_force_percentage,
    api_send_frame,
    use_xy_to_z_cross_term,
    bias_force_x,
):

    traj = move_along_trajectory(api_send_frame, velocity, world_T_goals)
    press_force = geometry_pb2.Vec3(x=0, y=0, z=press_force_percentage)

    max_vel = wrappers_pb2.DoubleValue(value=velocity)

    cmd = arm_surface_contact_pb2.ArmSurfaceContact.Request(
        pose_trajectory_in_task=traj,
        root_frame_name=api_send_frame,
        root_tform_task=world_T_admittance,
        press_force_percentage=press_force,
        x_axis=arm_surface_contact_pb2.ArmSurfaceContact.Request.AXIS_MODE_POSITION,
        y_axis=arm_surface_contact_pb2.ArmSurfaceContact.Request.AXIS_MODE_POSITION,
        z_axis=arm_surface_contact_pb2.ArmSurfaceContact.Request.AXIS_MODE_POSITION,
        max_linear_velocity=max_vel,
    )

    if is_admittance:
        # Add admittance options
        cmd.z_axis = arm_surface_contact_pb2.ArmSurfaceContact.Request.AXIS_MODE_FORCE
        cmd.press_force_percentage.z = press_force_percentage

        # if admittance_frame is not None:

        # Set the robot to be really stiff in x/y and really sensitive to admittance in z.
        cmd.xy_admittance = (
            arm_surface_contact_pb2.ArmSurfaceContact.Request.ADMITTANCE_SETTING_OFF
        )
        cmd.z_admittance = (
            arm_surface_contact_pb2.ArmSurfaceContact.Request.ADMITTANCE_SETTING_LOOSE
        )

        if use_xy_to_z_cross_term:
            cmd.xy_to_z_cross_term_admittance = (
                arm_surface_contact_pb2.ArmSurfaceContact.Request.ADMITTANCE_SETTING_VERY_STIFF
            )
        else:
            cmd.xy_to_z_cross_term_admittance = (
                arm_surface_contact_pb2.ArmSurfaceContact.Request.ADMITTANCE_SETTING_OFF
            )

        # Set a bias force
        cmd.bias_force_ewrt_body.CopyFrom(geometry_pb2.Vec3(x=bias_force_x, y=0, z=0))
    else:
        cmd.bias_force_ewrt_body.CopyFrom(geometry_pb2.Vec3(x=0, y=0, z=0))

    gripper_cmd_packed = RobotCommandBuilder.claw_gripper_open_fraction_command(0)
    cmd.gripper_command.CopyFrom(
        gripper_cmd_packed.synchronized_command.gripper_command.claw_gripper_command
    )

    cmd.is_robot_following_hand = allow_walking

    # Build the request proto
    proto = arm_surface_contact_service_pb2.ArmSurfaceContactCommand(request=cmd)

    # Send the request
    arm_surface_contact_client.arm_surface_contact_command(proto)


def get_transforms(use_vision_frame, robot_state):
    if not use_vision_frame:
        world_T_body = get_a_tform_b(
            robot_state.kinematic_state.transforms_snapshot, "odom", "body"
        )
    else:
        world_T_body = get_a_tform_b(
            robot_state.kinematic_state.transforms_snapshot, "vision", "body"
        )

    body_T_hand = get_a_tform_b(
        robot_state.kinematic_state.transforms_snapshot, "body", "hand"
    )
    world_T_hand = world_T_body * body_T_hand

    odom_T_body = get_a_tform_b(
        robot_state.kinematic_state.transforms_snapshot, "odom", "body"
    )

    return (world_T_body, body_T_hand, world_T_hand, odom_T_body)


def do_pause():
    input("Paused, press enter to continue...")

def resize_gcode_string(gcode_string, block_size=1):
    """
    WARNING: only handles G1/G0 commands
    """
    result = gcode_string

    try:
        max_x = 0
        max_y = 0

        # Find the maximum X and Y values in the G-code string
        lines = gcode_string.split('\n')
        for line in lines:
            if line.startswith('G1') or line.startswith('G0'):  # Look for movement commands
                parts = line.split()
                for part in parts:
                    if part.startswith('X'):
                        x_value = float(part[1:])
                        max_x = max(max_x, x_value)
                    elif part.startswith('Y'):
                        y_value = float(part[1:])
                        max_y = max(max_y, y_value)

        # Calculate the scaling factors
        scale_x = block_size / max_x
        scale_y = block_size / max_y

        # Scale the G-code string
        scaled_lines = []
        for idx, line in enumerate(lines):
            if idx == 1:
                scaled_lines.append('G00 Z-0.0025')
            if line.startswith('G1') or line.startswith('G0'):  # Look for movement commands
                parts = line.split()
                new_parts = []
                for part in parts:
                    if part.startswith('X'):
                        x_value = float(part[1:]) * scale_x
                        new_parts.append(f'X{x_value:.4f}')
                    elif part.startswith('Y'):
                        y_value = float(part[1:]) * scale_y
                        new_parts.append(f'Y{y_value:.4f}')
                    elif part.startswith('Z') and part != 'Z0.5':
                        new_parts.append('Z-0.0025')
                    else:
                        new_parts.append(part)
                scaled_lines.append(' '.join(new_parts))
            else:
                scaled_lines.append(line)

        scaled_lines.append('G0 X0.8 Y0.0 Z0.5')  # Move to the origin

        return '\n'.join(scaled_lines)
    except Exception as e:
        print(f'Error resizing G-code: {e}, traceback: {e.__traceback__}')

    return result