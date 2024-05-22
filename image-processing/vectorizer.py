from io import BytesIO, StringIO

from modal import (
    App,
    Image,
    web_endpoint,
)

vectorizer = (
    Image.debian_slim(python_version="3.11")
    .apt_install(
        "libglib2.0-0", "libsm6", "libxrender1", "libxext6", "ffmpeg", "libgl1"
    )
    .pip_install(
        "numpy",
        "pillow",
        "opencv-python",
        "svgpathtools",
        "svgwrite",
    )
)

app = App("vectorizer")

with vectorizer.imports():
    import numpy as np
    import modal
    import io
    import svgpathtools
    import base64
    import cv2
    import svgwrite

    from PIL import Image

@app.cls(container_idle_timeout=240, image=vectorizer)
class Model:

    def image_to_svg(self, pillow_image, stroke_width=7.0):
        # Convert Pillow image to numpy array
        np_image = np.array(pillow_image)

        # Convert to grayscale
        gray_image = cv2.cvtColor(np_image, cv2.COLOR_BGR2GRAY)

        # Apply GaussianBlur to reduce noise and improve edge detection
        blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)

        # Apply Canny edge detection
        edges = cv2.Canny(blurred_image, 90, 150)

        # Dilate edges to get thicker lines
        kernel = np.ones((3, 3), np.uint8)
        dilated_edges = cv2.dilate(edges, kernel, iterations=1)

        # Find contours from the dilated edges
        contours, _ = cv2.findContours(dilated_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Determine the bounds of all contours
        min_x, min_y = np.inf, np.inf
        max_x, max_y = -np.inf, -np.inf
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x + w)
            max_y = max(max_y, y + h)

        # Create SVG drawing with viewBox
        width = max_x - min_x
        height = max_y - min_y
        dwg = svgwrite.Drawing(viewBox=f"{min_x} {min_y} {width} {height}")

        # Add paths for each contour
        for contour in contours:
            path_data = "M " + " L ".join(f"{point[0][0]},{point[0][1]}" for point in contour)
            path_data += " Z"  # Add 'Z' to close the path
            dwg.add(dwg.path(d=path_data, fill="none", stroke="black", stroke_width=stroke_width))

        # Convert SVG drawing to byte stream
        svg_string_io = StringIO()
        dwg.write(svg_string_io)
        svg_string = svg_string_io.getvalue().encode('utf-8')
        svg_byte_stream = BytesIO(svg_string)
        svg_byte_stream.seek(0)

        return svg_byte_stream


    def _inference(self, item, max_lines=100):
        diffusion_function = modal.Function.lookup("stable-diffusion-xl", "Model.inference")

        img = diffusion_function.remote(item=item)

        # Convert byte stream to SVG
        img.seek(0)
        image = Image.open(img)
        svg = self.image_to_svg(image)

        gcode_output = self.svg_to_gcode(svg.getvalue())

        # Get the byte content
        img_byte_content = img.getvalue()

        # Encode the byte content to base64
        img_base64 = base64.b64encode(img_byte_content).decode('utf-8')
        # return json of gcode_output and SVG
        output = {
            "gcode": gcode_output,
            "svg": svg.getvalue(),
            "image": img_base64,
        }

        return output

    def svg_to_gcode(self, svg_data):
        # Use io.BytesIO to handle the byte stream
        svg_stream = io.BytesIO(svg_data)
        paths, attributes = svgpathtools.svg2paths(svg_stream)
        gcode = []

        matrix_of_coords = []  # code, x, y, z

        start_point = paths[0][0].start
        gcode.append(f"G00 X{start_point.real:.3f} Y{start_point.imag:.3f} Z0.5")  # Lift pen and move to start

        for path in paths:
            start_point = path[0].start
            last_x, last_y = start_point.real, start_point.imag
            matrix_of_coords.append(['G00', last_x, last_y, 0.5])

            for segment in path:
                if isinstance(segment, svgpathtools.Line):
                    x, y = segment.end.real, segment.end.imag 
                    matrix_of_coords.append(['G01', x, y, 0])
                    last_x, last_y = x, y

        for coord in matrix_of_coords:
            gcode.append(f"{coord[0]} X{coord[1]:.3f} Y{coord[2]:.3f} Z-0.500")

        gcode.append("G00 Z0.5")

        return gcode


    @web_endpoint()
    def web_inference(self, item, max_lines):
        return self._inference(item, int(max_lines))