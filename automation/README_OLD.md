# hackathon2024_team05
# automation for spot


## Setup

```bash
python3 -m venv venv

source venv/bin/activate

python3 -m pip install -r requirements.txt
```

**IMPORTANT**: Connect to Spot's wifi `spot-BD-03160009` (password in 1Password). Spot's IP is now `192.168.80.3`

```bash
export BOSDYN_CLIENT_USERNAME=user
export BOSDYN_CLIENT_PASSWORD=*** # password in 1Password
```

### E-Stop

To control spot, you require a estop

```bash
cd estop
python3 estop.py 192.168.80.3
```

The above assumes you are running in the same venv as above.

## Run it!

Modify the `gcode.cfg` file as needed. This includes a path to the `gcode/file.gcode` that we want to draw.

```bash
python3 gcode.py 192.168.80.3
```