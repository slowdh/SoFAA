import random
import string

import torch
from diffusers import StableDiffusionPipeline
from PIL import Image


class ArchiDiffusionModel:
    def __init__(self, design_model="prompthero/openjourney-v4", develop_model="prompthero/openjourney-v4", batch_size=4):
        self.batch_size = batch_size
        self.device = "cuda"
        self.precision = torch.float16
        self.num_inference_steps = 50
        self.random_name_len = 16
        self.save_path = "/home/fastdh/server/SoFAA/bot/imgs_generated"
        self.prompt_prefix = 'highly detailed, realism, denoised, single image, prize winner, modern, famous architect design, architecture design'

        self.design_model = self._get_design_model(design_model)
        # TODO: add develop model
        self.develop_model = develop_model

    def _get_design_model(self, model_name):
        pipe = StableDiffusionPipeline.from_pretrained(model_name, torch_dtype=self.precision)
        pipe = pipe.to(self.device)
        pipe.enable_xformers_memory_efficient_attention()
        return pipe
    
    def _get_design_inputs(self, prompt):                                                                                                                                                                                                                                                                                                                                                                    
        prompts = self.batch_size * [prompt]                                                                                                                                                                                                             
        return {"prompt": prompts, "num_inference_steps": self.num_inference_steps}   

    def _generate_random_names(self):
        return [''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(self.random_name_len)) for _ in range(self.batch_size)]
        
    def design(self, prompt):
        prompt = self.prompt_prefix + ', ' + prompt
        images = self.design_model(**self._get_design_inputs(prompt)).images
        names = self._generate_random_names()
        for img, name in zip(images, names):
            img.save(f"{self.save_path}/{name}.jpg")
