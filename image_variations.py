import torch
from diffusers import StableDiffusionImageVariationPipeline
from PIL import Image
from torchvision import transforms


# torch.backends.cudnn.benchmark = True
# torch.backends.cuda.matmul.allow_tf32 = True

device = "cuda"

pipe = StableDiffusionImageVariationPipeline.from_pretrained(
  "lambdalabs/sd-image-variations-diffusers",
  revision="v2.0",
  torch_dtype=torch.float16,
  )

pipe = pipe.to(device)
pipe.enable_xformers_memory_efficient_attention()
pipe.unet.to(memory_format=torch.channels_last)
# pipe.enable_attention_slicing()

# image preprocessing
im = Image.open("/home/fastdh/server/SoFAA/test_imgs/ast.png")
tform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Resize(
        (224, 224),
        interpolation=transforms.InterpolationMode.BICUBIC,
        antialias=False,
        ),
    transforms.Normalize(
      [0.48145466, 0.4578275, 0.40821073],
      [0.26862954, 0.26130258, 0.27577711]),
])
inp = tform(im).to(device).unsqueeze(0)

with torch.inference_mode():
  out = pipe(inp, guidance_scale=3)

out["images"][0].save("/home/fastdh/server/SoFAA/test_imgs/variation_result.jpg")
out["images"][0].show()
