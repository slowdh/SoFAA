import torch
from diffusers import StableDiffusionPipeline
from PIL import Image

device = "cuda"
precision = torch.float32
# precision = torch.float16

# model_id = "runwayml/stable-diffusion-v1-5"
model_id = "prompthero/openjourney-v4"
pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=precision)
pipe = pipe.to(device)
pipe.enable_xformers_memory_efficient_attention()

prompt = "a photo of an astronaut riding a horse"
image = pipe(prompt).images[0]  

image.save("/home/fastdh/server/SoFAA/test_imgs/ast.png")
# image["images"][0].show()