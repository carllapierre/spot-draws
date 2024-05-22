
import numpy as np

from bosdyn.client.math_helpers import Quat, SE3Pose, math

from application.services.gcode.gcode_helpers import make_orthogonal

class GCodeReader:

    def __init__(self, file, scale, logger, below_z_is_admittance, travel_z, draw_on_wall,
                 gcode_start_x=0, gcode_start_y=0):
        # open the file
        self.file = open(file, 'r')
        self.scale = scale
        self.logger = logger
        self.below_z_is_admittance = below_z_is_admittance
        self.travel_z = travel_z
        self.draw_on_wall = draw_on_wall
        self.gcode_start_x = gcode_start_x
        self.gcode_start_y = gcode_start_y

        self.current_origin_T_goals = None

        self.last_x = 0
        self.last_y = 0
        self.last_z = 0

    def set_origin(self, world_T_origin, world_T_admittance_frame):
        if not self.draw_on_wall:
            self.world_T_origin = SE3Pose(world_T_origin.x, world_T_origin.y, world_T_origin.z,
                                          world_T_origin.rot)

            # Ensure the origin is gravity aligned, otherwise we get some height drift.
            zhat = [0.0, 0.0, 1.0]
            (x1, x2, x3) = world_T_origin.rot.transform_point(-1.0, 0.0, 0.0)
            xhat_temp = [x1, x2, x3]
            xhat = make_orthogonal(zhat, xhat_temp)
            yhat = np.cross(zhat, xhat)
            mat = np.array([xhat, yhat, zhat]).transpose()

            self.world_T_origin.rot = Quat.from_matrix(mat)
        else:
            # Drawing on a wall, ensure that the rotation of the origin is aligned to the admittance
            # frame
            (x1, x2, x3) = world_T_admittance_frame.rot.transform_point(0, -1, 0)
            xhat = [x1, x2, x3]

            (y1, y2, y3) = world_T_admittance_frame.rot.transform_point(1, 0, 0)
            yhat = [y1, y2, y3]

            (z1, z2, z3) = world_T_admittance_frame.rot.transform_point(0, 0, 1)
            zhat = [z1, z2, z3]

            mat = np.array([xhat, yhat, zhat]).transpose()

            self.world_T_origin = SE3Pose(world_T_origin.x, world_T_origin.y, world_T_origin.z,
                                          Quat.from_matrix(mat))
            print(f'origin: {self.world_T_origin}')

    def get_origin_Q_goal(self):
        if not self.draw_on_wall:
            # Compute the rotation for the hand to point the x-axis of the gripper down.
            xhat = [0, 0, -1]  # [0.3162, 0, -0.9486]
            zhat = [-1, 0, 0]
            # (z1, z2, z3) = self.world_T_origin.rot.transform_point(0.0, 1.0, 0.0)
            # #(z1, z2, z3) = odom_T_body.rot.transform_point(1.0, 0.0, 0.0)
            # zhat_temp = [z1, z2, z3]
            # zhat = make_orthogonal(xhat, zhat_temp)

            yhat = np.cross(zhat, xhat)
            mat = np.array([xhat, yhat, zhat]).transpose()

            return Quat.from_matrix(mat)
        else:
            xhat = [0, 0, -1]
            yhat = [-1, 0, 0]
            zhat = [0, 1, 0]
            # (x1, x2, x3) = self.world_T_origin.rot.transform_point(0, 0, -1)
            # xhat = [x1, x2, x3]

            # (y1, y2, y3) = self.world_T_origin.rot.transform_point(-1, 0, 0)
            # yhat = [y1, y2, y3]

            # (z1, z2, z3) = self.world_T_origin.rot.transform_point(0, 1, 0)
            # zhat = [z1, z2, z3]

            mat = np.array([xhat, yhat, zhat]).transpose()
            origin_Q_goal = Quat.from_matrix(mat)

            return origin_Q_goal

    def convert_gcode_to_origin_T_goals(self, line):
        raw_line = line
        comments = ['(', '%', ';']

        for c in comments:
            # Remove anything after a comment
            first_comment = line.find(c)
            if first_comment >= 0:
                line = line[0:first_comment]

        array = line.split()

        if len(array) < 1:
            # Empty line
            return None

        if array[0] in ('G00', 'G01', 'G1', 'G0'):
            x = self.last_x
            y = self.last_y
            z = self.last_z
            for i in range(1, len(array)):
                if array[i][0] == 'X':
                    x = (float(array[i][1:]) - self.gcode_start_x) * self.scale
                elif array[i][0] == 'Y':
                    y = (float(array[i][1:]) - self.gcode_start_y) * self.scale
                elif array[i][0] == 'Z':
                    z = float(array[i][1:]) * self.scale
                elif array[i][0] == 'F':
                    f = float(array[i][1:]) * self.scale
                else:
                    self.logger.info('Warning, unknown parameter "%s" in line "%s"', array[i][0],
                                     raw_line)

            # Build a pose
            origin_T_goal = SE3Pose(x, y, z, self.get_origin_Q_goal())
            # self.logger.info('Translated "%s" to: (%s, %s, %s)', line.strip(), str(x), str(y), str(z))
            self.last_x = x
            self.last_y = y
            self.last_z = z

            return [origin_T_goal]

        elif array[0] in ('G02', 'G03', 'G2', 'G3'):
            # Circles
            x = self.last_x
            y = self.last_y
            z = self.last_z
            i_val = 0.0
            j_val = 0.0
            k_val = 0.0
            r = 0.0
            f = 0.0

            for i in range(1, len(array)):
                if array[i][0] == 'X':
                    x = (float(array[i][1:]) - self.gcode_start_x) * self.scale
                elif array[i][0] == 'Y':
                    y = (float(array[i][1:]) - self.gcode_start_y) * self.scale
                elif array[i][0] == 'Z':
                    z = float(array[i][1:]) * self.scale
                elif array[i][0] == 'I':
                    i_val = float(array[i][1:]) * self.scale
                elif array[i][0] == 'J':
                    j_val = float(array[i][1:]) * self.scale
                elif array[i][0] == 'K':
                    k_val = float(array[i][1:]) * self.scale
                elif array[i][0] == 'R':
                    r = float(array[i][1:]) * self.scale
                elif array[i][0] == 'F':
                    f = float(array[i][1:]) * self.scale
                else:
                    self.logger.info('Warning, unknown parameter "%s" in line "%s"', array[i][0],
                                     raw_line)

            if array[0] == 'G02':
                clockwise = True
            else:
                clockwise = False

            # Compute which plane we're on.
            assert i_val != 0 or j_val != 0 or k_val != 0

            xy_plane = False
            zx_plane = False
            yz_plane = False
            if abs(i_val) > 0 and abs(j_val) > 0:
                xy_plane = True
                last_p = [self.last_x, self.last_y]
                end_p = [x, y]
                center_p = np.add(last_p, [i_val, j_val])
            elif abs(i_val) > 0 and abs(k_val) > 0:
                zx_plane = True
                last_p = [self.last_x, self.last_z]
                end_p = [x, z]
                center_p = np.add(last_p, [i_val, k_val])
            elif abs(j_val) > 0 and abs(k_val) > 0:
                yz_plane = True
                last_p = [self.last_y, self.last_z]
                end_p = [y, z]
                center_p = np.add(last_p, [j_val, k_val])
            else:
                xy_plane = True
                last_p = [self.last_x, self.last_y]
                end_p = [x, y]
                center_p = np.add(last_p, [i_val, j_val])

            # Compute points along the arc
            res = 0.01  # radians

            # Convert to polar coordinates, where the origin in the circle's center
            last_rt_center = np.subtract(last_p, center_p)
            end_rt_center = np.subtract(end_p, center_p)

            last_r = math.sqrt(last_rt_center[0]**2 + last_rt_center[1]**2)
            last_theta = math.atan2(last_rt_center[1], last_rt_center[0])

            end_r = math.sqrt(end_rt_center[0]**2 + end_rt_center[1]**2)
            end_theta = math.atan2(end_rt_center[1], end_rt_center[0])

            tolerance = 0.1
            if abs(last_r - end_r) > tolerance:
                self.logger.info(
                    'GCODE WARNING: arc not valid: last_r - end_r is not zero: abs(last_r - end_r) = %s',
                    str(abs(last_r - end_r)))
            #assert abs(last_r - end_r) < tolerance

            # Sample between thetas.
            if clockwise:
                # theta is decreasing from last_theta to end_theta
                if last_theta < end_theta:
                    last_theta += 2.0 * math.pi
            else:
                # theta is increasing from last_theta to end_theta
                if last_theta > end_theta:
                    end_theta += 2.0 * math.pi

            num_samples = abs(int((end_theta - last_theta) / res))
            num_samples = max(num_samples, 1)

            x_out = []
            y_out = []
            z_out = []
            for i in range(0, num_samples - 1):
                if clockwise:
                    theta = last_theta - i * res
                else:
                    theta = last_theta + i * res
                r = last_r

                # To cartesian
                x = r * math.cos(theta)
                y = r * math.sin(theta)

                # Convert back to normal coordinates
                p = [x, y]
                p2 = np.add(p, center_p)

                if xy_plane:
                    x_out.append(p2[0])
                    y_out.append(p2[1])
                    z_out.append(self.last_z)
                elif zx_plane:
                    x_out.append(p2[0])
                    y_out.append(self.last_y)
                    z_out.append(p2[1])
                elif yz_plane:
                    x_out.append(self.last_x)
                    y_out.append(p2[0])
                    z_out.append(p2[1])

            # Add a point at the end so that we don't miss our end point because of sampling
            # resolution.
            if xy_plane:
                x_out.append(end_p[0])
                y_out.append(end_p[1])
                z_out.append(self.last_z)
            elif zx_plane:
                x_out.append(end_p[0])
                y_out.append(self.last_y)
                z_out.append(end_p[1])
            elif yz_plane:
                x_out.append(self.last_x)
                y_out.append(end_p[0])
                z_out.append(end_p[1])

            self.last_x = x_out[-1]
            self.last_y = y_out[-1]
            self.last_z = z_out[-1]

            # Convert points to poses
            se3_poses = []
            for i in range(0, len(x_out)):
                se3_poses.append(SE3Pose(x_out[i], y_out[i], z_out[i], self.get_origin_Q_goal()))

            return se3_poses

        else:
            self.logger.info('Unsupported gcode action: %s skipping.', line[0:2])
            return None

    def get_world_T_goal(self, origin_T_goal, ground_plane_rt_vo):
        if not self.draw_on_wall:
            world_T_goal = self.world_T_origin * origin_T_goal
            if not self.is_admittance():
                world_T_goal.z = self.travel_z + ground_plane_rt_vo[2]
            else:
                world_T_goal.z = ground_plane_rt_vo[2]
        else:
            # Drawing on a wall
            if not self.is_admittance():
                z_value_rt_origin = self.travel_z
            else:
                z_value_rt_origin = 0
            origin_T_goal2 = SE3Pose(
                origin_T_goal.x, origin_T_goal.y, origin_T_goal.z + z_value_rt_origin,
                Quat(origin_T_goal.rot.w, origin_T_goal.rot.x, origin_T_goal.rot.y,
                     origin_T_goal.rot.z))
            world_T_goal = self.world_T_origin * origin_T_goal2

        return (self.is_admittance(), world_T_goal)

    def is_admittance(self):
        # If we are below the z height in the gcode file, we are in admittance mode
        if self.current_origin_T_goals[0].z < self.below_z_is_admittance:
            return True
        else:
            return False

    def get_next_world_T_goals(self, ground_plane_rt_vo, read_new_line=True):
        origin_T_goals = None
        while not origin_T_goals:
            if read_new_line:
                self.last_line = self.file.readline()
                self.logger.info('Gcode: %s', self.last_line.strip())
            if not self.last_line:
                return (False, None, False)
            elif self.last_line.strip() == 'M0':
                return (False, None, True)
            origin_T_goals = self.convert_gcode_to_origin_T_goals(self.last_line)

        self.current_origin_T_goals = origin_T_goals

        world_T_goals = []
        for pose in self.current_origin_T_goals:
            (temp, world_T_goal) = self.get_world_T_goal(pose, ground_plane_rt_vo)
            world_T_goals.append(world_T_goal)

        return (self.is_admittance(), world_T_goals, False)

    def test_file_parsing(self):
        """Parse the file.

        Relies on any errors being logged by self.logger
        """
        for line in self.file:
            self.logger.debug('Line: %s', line.strip())
            self.convert_gcode_to_origin_T_goals(line)
