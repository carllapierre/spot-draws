# hackathon2024_team05
# automation for spot


## Setup

```bash
# From root of project
docker compose up
```

Visit `http://localhost:8080/` for a welcome message

Fire POST request with gcode:

```bash
curl -X POST http://localhost:8080/gcode -d "gcode=G00 Z5.0%0AG01 X0.0 Y0.0 Z-0.2%0AG01 X0.5 Y0.0%0AG01 X0.5 Y0.5%0AG01 X0.0 Y0.5%0AG01 X0.0 Y0.0"
```

## Run it

### Estop required

```bash
python3 -m venv venv

source venv/bin/activate

python3 estop/estop.py 192.168.80.3
```

From another terminal window, run:

```bash
curl -X POST http://localhost:8080/gcode -d "gcode=G00 Z5.0%0AG01 X0.0 Y0.0 Z-0.2%0AG01 X0.5 Y0.0%0AG01 X0.5 Y0.5%0AG01 X0.0 Y0.5%0AG01 X0.0 Y0.0"
```

## Resources

GCode Simulator - https://nraynaud.github.io/webgcode/
Spot Stopper - http://localhost:8080/stop