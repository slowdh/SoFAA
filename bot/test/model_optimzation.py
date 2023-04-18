import os
import random
import string
import time

import torch
from diffusers import StableDiffusionPipeline


class ArchiDiffusionModel:
    def __init__(self, design_model=None, develop_model=None, batch_size=4, num_inference_steps=25, save_path=None):
        self.batch_size = batch_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.precision = torch.float16
        self.num_inference_steps = num_inference_steps
        self.random_name_len = 16
        self.save_path = save_path
        self.prompt_prefix = 'highly detailed, realism, denoised, single image, prize winner, modern, famous architect design, architecture design'

        if design_model is None:
            design_model = "prompthero/openjourney-v4"
        self.design_model = self._get_design_model(design_model)

    def _get_design_model(self, model_name):
        pipe = StableDiffusionPipeline.from_pretrained(model_name, torch_dtype=self.precision)
        pipe = pipe.to(self.device)
        pipe.enable_xformers_memory_efficient_attention()
        pipe.enable_vae_slicing()
        pipe.unet.to(memory_format=torch.channels_last)
        pipe.unet = torch.compile(pipe.unet)

        return pipe

    def _generate_random_names(self):
        return [''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(self.random_name_len)) for _ in range(self.batch_size)]
        
    def design(self, prompt, steps=None, image_prefix=None):
        if steps is None:
            steps = self.num_inference_steps
        prompts = [self.prompt_prefix + ', ' + prompt] * self.batch_size
        images = self.design_model(prompt=prompts, num_inference_steps=steps).images

        names = self._generate_random_names()
        for img, name in zip(images, names):
            if image_prefix:
                name = f"{image_prefix}-{name}"
            img.save(f"{self.save_path}/{name}.jpg")

        return names


if __name__ == '__main__':
    prompt = "design swimming pool in baroque style building, inside, highly detailed, eye level"
    save_path = "/home/fastdh/server/SoFAA/bot/test/imgs_generated"
    model = ArchiDiffusionModel(save_path=save_path)

    PREFIX ="unet_compiled"
    model.design(prompt, steps=50, image_prefix=PREFIX)

    tic = time.time()
    model.design(prompt, steps=50, image_prefix=PREFIX)
    print(f"{time.time() - tic:.2f}s")
    
    
    """
    spec::::
    [0] unet_compiled-xformer_vae-slicing_channel-last 7.39s 7.08it/s
    [1] unet_compiled: 7.60s, 6.92it/s
    [2] vae-slicing: 8.54s, 6.34it/s
    [3] xformer + fp16: 8.59s, 6.33it/s
    [4] fp16: 8.60s, 6.32it/s
    [5] channels_last: 8.67s, 6.28it/s
    [6] attention-slicing: 11.24s 4.73it/s
    """