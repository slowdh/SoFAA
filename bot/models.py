import os
import random
import string

import torch
from diffusers import StableDiffusionPipeline
from diffusers import StableDiffusionImageVariationPipeline
from torchvision import transforms
from PIL import Image


class ArchiDiffusionModel:
    def __init__(self, design_model=None, develop_model=None, batch_size=4, num_inference_steps=25):
        self.batch_size = batch_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.precision = torch.float16
        self.num_inference_steps = num_inference_steps
        self.random_name_len = 16
        self.save_path = "/home/fastdh/server/SoFAA/bot/imgs_generated"
        self.prompt_prefix = 'highly detailed, realism, denoised, single image, prize winner, modern, famous architect design, architecture design'

        if design_model is None:
            design_model = "prompthero/openjourney-v4"
        if develop_model is None:
            develop_model = "lambdalabs/sd-image-variations-diffusers"
        self.design_model = self._get_design_model(design_model)
        self.develop_model = self._get_develop_model(develop_model)

    def _get_design_model(self, model_name):
        pipe = StableDiffusionPipeline.from_pretrained(model_name, torch_dtype=self.precision)
        pipe = pipe.to(self.device)
        pipe.enable_xformers_memory_efficient_attention()

        return pipe

    def _get_develop_model(self, model_name):
        pipe = StableDiffusionImageVariationPipeline.from_pretrained(
            model_name,
            revision="v2.0",
            torch_dtype=torch.float16,
            )
        pipe = pipe.to(self.device)
        pipe.enable_xformers_memory_efficient_attention()
        # pipe.unet.to(memory_format=torch.channels_last)
        # pipe.enable_attention_slicing()

        return pipe

    def _generate_random_names(self):
        return [''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(self.random_name_len)) for _ in range(self.batch_size)]
        
    def design(self, prompt, steps=None):
        if steps is None:
            steps = self.num_inference_steps
        prompts = [self.prompt_prefix + ', ' + prompt] * self.batch_size
        images = self.design_model(prompt=prompts, num_inference_steps=steps).images
        names = self._generate_random_names()
        for img, name in zip(images, names):
            img.save(f"{self.save_path}/{name}.jpg")

        return names
    
    def develop(self, image_id, steps=None):
        if steps is None:
            steps = self.num_inference_steps
        
        img_path = os.path.join(self.save_path, f"{image_id}.jpg")
        im = Image.open(img_path)
        images = self.develop_model([im] * self.batch_size, guidance_scale=3, num_inference_steps=steps).images
        names = self._generate_random_names()
        for img, name in zip(images, names):
            img.save(f"{self.save_path}/{name}.jpg")

        return names

    def run(self, task_queue, processed_queue):
        while True:
            task = task_queue.get()

            prompt = task['prompt']
            if task['type'] == 'design':
                img_names = self.design(prompt)
            else:
                img_names = self.develop(prompt)

            task["img_names"] = img_names
            processed_queue.put(task)
            # TODO: maybe not needed, since not using join method
            task_queue.task_done()
