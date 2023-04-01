import torch
from diffusers import StableDiffusionPipeline
from PIL import Image


def get_inputs(batch_size=1):
    generator = [torch.Generator("mps").manual_seed(i) for i in range(batch_size)]
    prompts = batch_size * [prompt]
    num_inference_steps = 25

    return {
        "prompt": prompts,
        "generator": generator,
        "num_inference_steps": num_inference_steps,
    }

def image_grid(imgs, rows=2, cols=2):
    w, h = imgs[0].size
    grid = Image.new("RGB", size=(cols * w, rows * h))

    for i, img in enumerate(imgs):
        grid.paste(img, box=(i % cols * w, i // cols * h))
    return grid


if __name__ == '__main__':
    pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
    pipe = pipe.to("mps")

    # Recommended if your computer has < 64 GB of RAM
    pipe.enable_attention_slicing()

    prompt1 = "a photo of an astronaut riding a horse on mars"
    prompt2 = "interior 3d render coastal style, with white walls, where the ceiling is curved, kitchen only with bottom cabinets, cabinets of light wood color. There's also a kitchen island with a golden faucet and in front a large white table with wodden chairs with two black bowls on the top. The sun is almost rising"
    prompt3 = "Architecture design by El Lissitzky"

    prompt = prompt3
    
    # First-time "warmup" pass (see explanation above)
    _ = pipe(prompt, num_inference_steps=1)

    # for simgle image
    # Results match those from the CPU device after the warmup pass.
    image = pipe(prompt).images[0]
    image.show()
    image.save(f"./test_imgs/astronaut_rides_horse.png")

    # for batched images
    images = pipe(**get_inputs(batch_size=4)).images
    grid = image_grid(images)
    grid.show()
    grid.save(f"./test_imgs/grid.png")
