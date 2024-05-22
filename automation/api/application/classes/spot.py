import os

from bosdyn.client import ResponseError, RpcError, create_standard_sdk
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
from bosdyn.client.robot_command import RobotCommandClient
from bosdyn.client.util import authenticate
from ping3 import ping


class Spot:
    """
    Spot Robot
    """

    def __init__(self):
        super().__init__()
        self.robot = self.create_and_auth_robot()
        self.lease = None
        self.robot_id = None

        if self.robot:
            # Clients
            self.command_client = self.robot.ensure_client(
                RobotCommandClient.default_service_name
            )
            self.lease_client = self.robot.ensure_client(
                LeaseClient.default_service_name
            )

            # Leases
            self.lease_wallet = self.lease_client.lease_wallet
            self.lease_keepalive = None

    def create_and_auth_robot(self):
        """
        Kicks off setup of robot
        """
        robot = None

        try:
            sdk_name = os.getenv("SDK_NAME")
            robot_ip = os.getenv("ROBOT_IP")

            if robot_ip is not None:
                robot_ping = ping(robot_ip)
                if robot_ping is None or robot_ping is False:
                    print(
                        f"Machine is unable to see robot at {robot_ip}, skipping Spot.create_and_auth_robot..."
                    )
                    return None
            else:
                print(
                    "No ROBOT_IP was provided, unable to create and auth with robot..."
                )
                return None

            print(f"Create SDK: {sdk_name}")
            sdk = create_standard_sdk(sdk_name)

            print(f"Create robot at {robot_ip}")
            robot = sdk.create_robot(robot_ip)

            authenticate(robot)
            print("Authenticated with robot")

            robot.time_sync.wait_for_sync()
        except Exception as exc:
            print("Unable to create and authenticate robot. Exception is: %s" % exc)

        return robot

    def release_lease(self):
        """
        Release the lease on Spot
        """
        self.lease_client.return_lease(self.lease)
        self.lease = None

    def obtain_lease(self):
        """
        Obtains lease on robot
        """
        self.lease = self.lease_client.acquire()
        self.lease_keepalive = LeaseKeepAlive(self.lease_client)

        print("Obtained lease")

    def claim(self):
        """
        Claim the robot
        """
        if self.robot_id is not None:
            return True, "Already claimed"

        try:
            self.robot_id = self.robot.get_id()
            self.obtain_lease()
            return True, "Successfully claimed"
        except (ResponseError, RpcError) as err:
            print("Unable to obtain lease e: %s" % err)
            return False, str(err)

    def disconnect(self):
        """
        Release control of robot
        """
        if self.robot.time_sync:
            self.robot.time_sync.stop()
        self.release_lease()

    def power_off(self):
        """
        Release control of robot
        """

        if (self.lease):
            self.lease = self.lease_client.take()
            self.robot.power_off(cut_immediately=False, timeout_sec=20)
            assert self.robot.power_on_state is False, "Robot did not power off"
            self.release_lease()
        else:
            self.lease = self.lease_client.take()
            self.robot.power_off(cut_immediately=False, timeout_sec=20)
            self.release_lease()

spot = Spot()
