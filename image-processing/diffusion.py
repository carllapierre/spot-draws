from io import BytesIO, StringIO
from pathlib import Path

from modal import (
    App,
    Image,
    Mount,
    asgi_app,
    build,
    enter,
    gpu,
    method,
    web_endpoint,
)

sdxl_image = (
    Image.debian_slim(python_version="3.11")
    .apt_install(
        "libglib2.0-0", "libsm6", "libxrender1", "libxext6", "ffmpeg", "libgl1"
    )
    .pip_install(
        "diffusers==0.26.3",
        "invisible_watermark==0.2.0",
        "transformers~=4.38.2",
        "accelerate==0.27.2",
        "safetensors==0.4.2",
        "opencv-python",
        "numpy",
        "svgwrite",
        "svgpathtools",
        "pillow"
    )
)

app = App(
    "stable-diffusion-xl"
)

with sdxl_image.imports():
    import torch
    from diffusers import DiffusionPipeline
    from fastapi import Response
    import cv2
    import numpy as np
    from PIL import Image
    import svgwrite

@app.cls(gpu=gpu.H100(), keep_warm=True, image=sdxl_image)
class Model:
    @build()
    def build(self):
        from huggingface_hub import snapshot_download

        ignore = [
            "*.bin",
            "*.onnx_data",
            "*/diffusion_pytorch_model.safetensors",
        ]
        snapshot_download(
            "stabilityai/stable-diffusion-xl-base-1.0", ignore_patterns=ignore
        )
        snapshot_download(
            "stabilityai/stable-diffusion-xl-refiner-1.0",
            ignore_patterns=ignore,
        )

    @enter()
    def enter(self):
        load_options = dict(
            torch_dtype=torch.float16,
            use_safetensors=True,
            variant="fp16",
            device_map="auto",
        )

        # Load base model
        self.base = DiffusionPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0", **load_options
        )

        # Load refiner model
        self.refiner = DiffusionPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-refiner-1.0",
            text_encoder_2=self.base.text_encoder_2,
            vae=self.base.vae,
            **load_options,
        )

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
            dwg.add(dwg.path(d=path_data, fill="none", stroke="black", stroke_width=stroke_width))

        # Convert SVG drawing to byte stream
        svg_string_io = StringIO()
        dwg.write(svg_string_io)
        svg_string = svg_string_io.getvalue().encode('utf-8')
        svg_byte_stream = BytesIO(svg_string)
        svg_byte_stream.seek(0)

        return svg_byte_stream

    def _inference(self, item, n_steps=35, high_noise_frac=0.9):
        negative_prompt = "deformed, uncentered, detailed, complex, patterned, textured background, colorful, noisy"
        prompt_template = f'simple icon representing an outline of a {item} on a white background'

        print("Prompt template:", prompt_template)
        image = self.base(
            guidance_scale=20,
            prompt=prompt_template,
            negative_prompt=negative_prompt,
            num_inference_steps=n_steps,
            denoising_end=high_noise_frac,
            output_type="latent",
        ).images
        image = self.refiner(
            prompt=prompt_template,
            negative_prompt=negative_prompt,
            num_inference_steps=n_steps,
            denoising_start=high_noise_frac,
            image=image,
        ).images[0]

        print("Image shape:", image)


        svg_byte_stream = self.image_to_svg(image)
        
        img_byte_stream = BytesIO()
        image.save(img_byte_stream, format="JPEG")

        return svg_byte_stream, img_byte_stream


    @method()
    def inference(self, item, n_steps=24, high_noise_frac=0.8):
        return self._inference(
            item, n_steps=n_steps, high_noise_frac=high_noise_frac
        )