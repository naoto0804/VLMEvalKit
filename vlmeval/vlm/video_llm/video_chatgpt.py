import torch
import os
import warnings
import copy as cp
import numpy as np
import sys
from ..base import BaseModel
from ...smp import isimg, listinstr
from ...dataset import DATASET_TYPE
from huggingface_hub import snapshot_download


class VideoChatGPT(BaseModel):
    INSTALL_REQ = True
    INTERLEAVE = False
    VIDEO_LLM = True

    def __init__(self, model_path='Video-ChatGPT/video_chatgpt-7B.bin', dir_root=None, **kwargs):
        assert model_path is not None
        sys.path.append(dir_root)
        try:
            from video_chatgpt.eval.model_utils import initialize_model
        except:
            warnings.warn(
                'Please first install requirements and set the root path to use Video-ChatGPT. \
                Follow the instructions at https://github.com/mbzuai-oryx/Video-ChatGPT.'
            )
            sys.exit(-1)
        model_name = snapshot_download('mmaaz60/LLaVA-7B-Lightening-v1-1')
        projection_name = 'video_chatgpt-7B.bin'
        projection_path = os.path.join(model_path, projection_name)
        if not os.path.exists(projection_path):
            warnings.warn(
                f'Video-ChatGPT Model {model_path} does not exist. \
                    Please download from https://github.com/mbzuai-oryx/Video-ChatGPT.'
            )
            sys.exit(-1)
        model, vision_tower, tokenizer, image_processor, video_token_len = initialize_model(
            model_name, projection_path
        )
        self.tokenizer = tokenizer
        self.model = model
        self.processor = image_processor
        self.context_len = video_token_len
        self.kwargs = kwargs
        self.vision_tower = vision_tower
        self.nframe = 8

    def get_model_output(self, model, video_processor, tokenizer, video, qs):
        from video_chatgpt.eval.model_utils import load_video
        from video_chatgpt.inference import video_chatgpt_infer
        conv_mode = 'video-chatgpt_v1'

        video_frames = load_video(video)

        # Run inference on the video and add the output to the list
        output = video_chatgpt_infer(
            video_frames,
            qs,
            conv_mode,
            model,
            self.vision_tower,
            tokenizer,
            video_processor,
            self.context_len,
        )
        return output

    def generate_inner(self, message, dataset=None):
        question, video = self.message_to_promptvideo(message)
        response = self.get_model_output(self.model, self.processor, self.tokenizer, video, question)
        return response
