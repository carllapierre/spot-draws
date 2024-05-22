class NoRobotError(Exception):
    """
    Exception to raise when spot.robot is None but needed
    """

    def __init__(self, msg="No authenticated robot", *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
