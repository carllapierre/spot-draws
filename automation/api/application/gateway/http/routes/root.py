from flask import request
from application.app import app
from application.classes.spot import Spot
from application.services.gcode_service import GCodeService
from application.services.gcode.gcode_helpers import resize_gcode_string

@app.route("/", methods=["GET"])
def root():
    """
    GET /
    ---
    responses:
        200:
            description: Simple return to show api is up and running
    """
    return "Up and running..."


@app.route("/gcode", methods=["GET", "POST"])
def gcode():
    """
    POST /gcode
    ---
    responses:
        200:
            description: Runs the gcode script...
    """

    # TODO: Remove requires_spot=False
    gcodeService = GCodeService(requires_spot=False)

    result = None
    try:
        if (gcodeService.robot is not None):
            # Verify the robot has an arm.
            assert gcodeService.robot.has_arm(), 'Robot requires an arm to run the gcode example.'

            # Verify the robot is not estopped and that an external application has registered and holds
            # an estop endpoint.
            assert not gcodeService.robot.is_estopped(), 'Robot is estopped. Please use an external E-Stop client, ' \
                                            'such as the estop SDK example, to configure E-Stop.'

        gcode_src = request.form.get('gcode', None)

        result = gcodeService.run_gcode(
            gcode_src=gcode_src,
            test_file_parsing=False
        )
    except Exception as e:
        error_msg = f'Error running gcode: {e}, traceback: {e.__traceback__}'
        if (gcodeService.robot is not None):
            gcodeService.robot.logger.error(error_msg)
        else:
            print(error_msg)

        return str(e)

    return result


@app.route("/stop", methods=["GET"])
def stop():
    """
    GET /
    ---
    responses:
        200:
            description: Simple return to show api is up and running
    """
    spot = Spot()
    spot.power_off()
    assert not spot.robot.is_powered_on(), "Robot power off failed."

    return "Robot is powered off."

