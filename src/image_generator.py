"""
Image Generator Module
Handles image generation using ComfyUI API for news headlines.
"""

import json
import logging
import requests
import websocket
import threading
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import base64
import io
from PIL import Image


class ImageGenerator:
    """Generates images using ComfyUI API."""
    
    def __init__(self, config: Dict):
        """Initialize image generator with ComfyUI configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # ComfyUI server settings
        self.server_address = config.get('server_address', '127.0.0.1:8188')
        self.base_url = f"http://{self.server_address}"
        self.ws_url = f"ws://{self.server_address}/ws"
        
        # Image generation settings
        self.output_dir = Path(config.get('output_dir', 'output/images'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load workflow template
        self.workflow_path = config.get('workflow_path', 'workflows/news_image.json')
        self.default_workflow = self._load_default_workflow()
        
        # Generation parameters
        self.default_params = {
            'width': config.get('width', 512),
            'height': config.get('height', 512),
            'steps': config.get('steps', 25),
            'cfg_scale': config.get('cfg_scale', 7.0),
            'sampler': config.get('sampler', 'dpmpp_2m'),
            'scheduler': config.get('scheduler', 'karras'),
            'seed': config.get('seed', -1)  # -1 for random
        }
        
    def generate_from_headline(self, headline: str, style: str = "news illustration") -> Optional[str]:
        """Generate an image from a news headline."""
        try:
            # Create enhanced prompt
            prompt = self._create_prompt_from_headline(headline, style)
            negative_prompt = self.config.get('negative_prompt', 
                                            "ugly, deformed, blurry, bad anatomy, low quality")
            
            self.logger.info(f"Generating image for headline: {headline[:50]}...")
            
            # Generate image
            image_data = self._generate_image(prompt, negative_prompt)
            
            if image_data:
                # Save image
                filename = self._create_filename(headline)
                image_path = self.output_dir / filename
                
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                self.logger.info(f"Image saved: {image_path}")
                return str(image_path)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating image for headline: {e}")
            return None
    
    def _create_prompt_from_headline(self, headline: str, style: str) -> str:
        """Create an enhanced prompt from headline."""
        # Load prompt templates
        prompt_templates = self.config.get('prompt_templates', {
            'news': "{headline}, {style}, professional, high quality, detailed",
            'funny': "{headline}, funny, cartoon style, humorous, meme-worthy, comedy",
            'artistic': "{headline}, artistic interpretation, abstract, creative, modern art",
            'realistic': "{headline}, photorealistic, documentary style, journalistic"
        })
        
        # Choose template based on style
        template_key = 'news'
        if 'funny' in style.lower() or 'humor' in style.lower():
            template_key = 'funny'
        elif 'art' in style.lower():
            template_key = 'artistic'
        elif 'realistic' in style.lower() or 'photo' in style.lower():
            template_key = 'realistic'
        
        template = prompt_templates.get(template_key, prompt_templates['news'])
        
        # Clean headline for prompt
        clean_headline = headline.replace('"', '').replace("'", "").strip()
        
        return template.format(headline=clean_headline, style=style)
    
    def _generate_image(self, prompt: str, negative_prompt: str = "") -> Optional[bytes]:
        """Generate image using ComfyUI API."""
        try:
            # Create workflow with prompts
            workflow = self._create_workflow(prompt, negative_prompt)
            
            # Queue prompt
            response = self._queue_prompt(workflow)
            if not response:
                return None
            
            prompt_id = response.get('prompt_id')
            if not prompt_id:
                self.logger.error("No prompt_id received")
                return None
            
            # Wait for completion and get result
            return self._wait_for_completion(prompt_id)
            
        except Exception as e:
            self.logger.error(f"Image generation error: {e}")
            return None
    
    def _create_workflow(self, prompt: str, negative_prompt: str) -> Dict:
        """Create ComfyUI workflow with given prompts."""
        # Try to load custom workflow, fall back to default
        try:
            if Path(self.workflow_path).exists():
                with open(self.workflow_path, 'r') as f:
                    workflow = json.load(f)
            else:
                workflow = self.default_workflow.copy()
        except Exception as e:
            self.logger.warning(f"Could not load workflow file: {e}, using default")
            workflow = self.default_workflow.copy()
        
        # Update workflow with prompts and parameters
        self._update_workflow_params(workflow, prompt, negative_prompt)
        
        return workflow
    
    def _update_workflow_params(self, workflow: Dict, prompt: str, negative_prompt: str):
        """Update workflow with current parameters."""
        # Find and update text nodes - using the new workflow structure
        for node_id, node in workflow.items():
            if node.get('class_type') == 'CLIPTextEncode':
                inputs = node.get('inputs', {})
                # Node 6 is positive prompt, Node 7 is negative prompt
                if node_id == '6':
                    inputs['text'] = prompt
                elif node_id == '7':
                    inputs['text'] = negative_prompt
            
            elif node.get('class_type') == 'EmptyLatentImage':
                inputs = node.get('inputs', {})
                inputs.update({
                    'width': self.default_params['width'],
                    'height': self.default_params['height']
                })
            
            elif node.get('class_type') == 'KSampler':
                inputs = node.get('inputs', {})
                inputs.update({
                    'steps': self.default_params['steps'],
                    'cfg': self.default_params['cfg_scale'],
                    'sampler_name': self.default_params['sampler'],
                    'scheduler': self.default_params['scheduler']
                })
                if self.default_params['seed'] >= 0:
                    inputs['seed'] = self.default_params['seed']
    
    def _queue_prompt(self, workflow: Dict) -> Optional[Dict]:
        """Queue prompt to ComfyUI server."""
        try:
            url = f"{self.base_url}/prompt"
            data = {"prompt": workflow}
            
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to queue prompt: {e}")
            return None
    
    def _wait_for_completion(self, prompt_id: str, timeout: int = 900) -> Optional[bytes]:
        """Wait for image generation completion and retrieve result."""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Check if generation is complete
                status = self._check_status(prompt_id)
                
                if status == 'completed':
                    return self._get_generated_image(prompt_id)
                elif status == 'failed':
                    self.logger.error(f"Generation failed for prompt {prompt_id}")
                    return None
                
                time.sleep(2)  # Wait 2 seconds before checking again
            
            self.logger.error(f"Generation timeout for prompt {prompt_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error waiting for completion: {e}")
            return None
    
    def _check_status(self, prompt_id: str) -> str:
        """Check generation status."""
        try:
            url = f"{self.base_url}/history/{prompt_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                history = response.json()
                if prompt_id in history:
                    return 'completed'
            
            # Check queue
            queue_url = f"{self.base_url}/queue"
            queue_response = requests.get(queue_url, timeout=10)
            if queue_response.status_code == 200:
                queue_data = queue_response.json()
                
                # Check if still in queue
                for item in queue_data.get('queue_running', []) + queue_data.get('queue_pending', []):
                    if item[1] == prompt_id:
                        return 'running'
            
            return 'unknown'
            
        except Exception as e:
            self.logger.error(f"Status check error: {e}")
            return 'unknown'
    
    def _get_generated_image(self, prompt_id: str) -> Optional[bytes]:
        """Retrieve generated image from ComfyUI."""
        try:
            url = f"{self.base_url}/history/{prompt_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            history = response.json()
            if prompt_id not in history:
                return None
            
            # Find output images
            outputs = history[prompt_id].get('outputs', {})
            for node_output in outputs.values():
                if 'images' in node_output:
                    for image_info in node_output['images']:
                        filename = image_info.get('filename')
                        if filename:
                            return self._download_image(filename)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting generated image: {e}")
            return None
    
    def _download_image(self, filename: str) -> Optional[bytes]:
        """Download image file from ComfyUI server."""
        try:
            url = f"{self.base_url}/view"
            params = {'filename': filename}
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            self.logger.error(f"Error downloading image: {e}")
            return None
    
    def _create_filename(self, headline: str) -> str:
        """Create a filename from headline."""
        # Clean headline for filename
        clean_headline = "".join(c for c in headline if c.isalnum() or c in (' ', '-', '_')).strip()
        clean_headline = clean_headline.replace(' ', '_')[:50]  # Limit length
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{clean_headline}.png"
    
    def _load_default_workflow(self) -> Dict:
        """Load or create default ComfyUI workflow."""
        default_workflow = {
            "1": {
                "inputs": {"text": "positive prompt", "clip": ["4", 1]},
                "class_type": "CLIPTextEncode"
            },
            "2": {
                "inputs": {"text": "negative prompt", "clip": ["4", 1]},
                "class_type": "CLIPTextEncode"
            },
            "3": {
                "inputs": {"seed": 0, "steps": 25, "cfg": 7.0, "sampler_name": "dpmpp_2m",
                          "scheduler": "karras", "denoise": 1.0, "model": ["4", 0],
                          "positive": ["1", 0], "negative": ["2", 0], "latent_image": ["5", 0]},
                "class_type": "KSampler"
            },
            "4": {
                "inputs": {"ckpt_name": "dreamshaper_8.safetensors"},
                "class_type": "CheckpointLoaderSimple"
            },
            "5": {
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
                "class_type": "EmptyLatentImage"
            },
            "6": {
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
                "class_type": "VAEDecode"
            },
            "7": {
                "inputs": {"filename_prefix": "news_image", "images": ["6", 0]},
                "class_type": "SaveImage"
            }
        }
        
        return default_workflow
