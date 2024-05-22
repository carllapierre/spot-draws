from io import BytesIO

from modal import (
    App,
    Image,
    build,
    enter,
    gpu,
    method,
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
    )
)

app = App(
    "stable-diffusion-xl"
)

with sdxl_image.imports():
    import torch
    from diffusers import DiffusionPipeline
    from PIL import Image
@app.cls(gpu=gpu.A10G(), container_idle_timeout=240, image=sdxl_image)
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

        self.base = DiffusionPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0", **load_options
        )

        self.refiner = DiffusionPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-refiner-1.0",
            text_encoder_2=self.base.text_encoder_2,
            vae=self.base.vae,
            **load_options,
        )

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

        img_byte_stream = BytesIO()
        image.save(img_byte_stream, format="JPEG")

        return img_byte_stream

    @method()
    def inference(self, item, n_steps=24, high_noise_frac=0.8):
        return self._inference(item, n_steps=n_steps, high_noise_frac=high_noise_frac)