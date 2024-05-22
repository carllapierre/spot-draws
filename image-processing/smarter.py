from io import BytesIO, StringIO
from pathlib import Path

from modal import (
    App,
    Image,
    web_endpoint,
)

smart_diffusion = (
    Image.debian_slim(python_version="3.11")
    .apt_install(
        "libglib2.0-0", "libsm6", "libxrender1", "libxext6", "ffmpeg", "libgl1"
    )
    .pip_install(
        "numpy",
        "pillow",
        "opencv-python",
        "svgpathtools",
    )
)

app = App(
    "smart-diffusion-xl"
)

with smart_diffusion.imports():
    import numpy as np
    from PIL import Image
    import modal
    import io
    import svgpathtools
    import base64

@app.cls(keep_warm=True, image=smart_diffusion)
class Model:
    def _inference(self, item, max_lines=100):
        num_runs = 5
        f = modal.Function.lookup("stable-diffusion-xl", "Model.inference")

        svg, img, no_bg = f.remote(item=item)

        print ("SVG: ", svg)
        print ("IMG: ", img)
        gcode_output = self.svg_to_gcode(svg.getvalue(), max_lines)

        img.seek(0)
        no_bg.seek(0)

        # Get the byte content
        img_byte_content = img.getvalue()
        no_bg_byte_content = no_bg.getvalue()

        # Encode the byte content to base64
        img_base64 = base64.b64encode(img_byte_content).decode('utf-8')
        no_bg_base64 = base64.b64encode(no_bg_byte_content).decode('utf-8')
        # return json of gcode_output and SVG
        output = {
            "gcode": gcode_output,
            "svg": svg.getvalue(),
            "image": img_base64,
            "no_bg_image": no_bg_base64
        }

        return output

    def svg_to_gcode(self, svg_data, max_lines=100):
        # Use io.BytesIO to handle the byte stream
        svg_stream = io.BytesIO(svg_data)
        paths, attributes = svgpathtools.svg2paths(svg_stream)
        gcode = []

        # Take note of initial position
        initial_x = paths[0][0].start.real
        initial_y = paths[0][0].start.imag
        lowest_x = initial_x
        lowest_y = initial_y

        print(f"Initial X: {initial_x}, Initial Y: {initial_y}")

        matrix_of_coords = []  # code, x, y, z
        total_segments = sum(len(path) for path in paths)

        # Determine if skipping is needed and calculate skip interval
        iter = 2 if total_segments > max_lines else 1  # Always process at least every second line if skipping is needed
        skip = 0  # Start with no skipping

        if total_segments > max_lines:
            skip = total_segments // (max_lines*0.6)

        print(f"Total segments: {total_segments}, Iter: {iter}, Skip: {skip}")

        line_count = 0
        skip_count = 0

        for path in paths:
            start_point = path[0].start
            last_x, last_y = (start_point.real - initial_x), (start_point.imag - initial_y)
            matrix_of_coords.append(['G00', last_x, last_y, 0.5])

            for segment in path:
                if skip_count < skip and (line_count % iter == 0):
                    skip_count += 1
                    continue  # Skip the current line of G-code

                if skip_count == skip:
                    skip_count = 0  # Reset skip count after skipping the specified number of lines

                if isinstance(segment, svgpathtools.Line):
                    x, y = (segment.end.real - initial_x), (segment.end.imag - initial_y)
                    matrix_of_coords.append(['G01', x, y, 0])
                    last_x, last_y = x, y
                    if x < lowest_x:
                        lowest_x = x
                    if y < lowest_y:
                        lowest_y = y

                line_count += 1  # Increment the line count after processing a line

        gcode.append(f"G00 X{initial_x:.3f} Y{initial_y:.3f} Z0.5")  # Lift pen and move to start
        for coord in matrix_of_coords:
            new_x = coord[1]
            new_y = coord[2]
            # Only offset if value is negative
            if lowest_x < 0:
                new_x = coord[1] - lowest_x
            if lowest_y < 0:
                new_y = coord[2] - lowest_y

            gcode.append(f"{coord[0]} X{new_x:.3f} Y{new_y:.3f} Z-0.500")
        gcode.append("G00 Z0.5")

        return gcode


    @web_endpoint()
    def web_inference(self, item, max_lines):
        return self._inference(item, int(max_lines))