import requests
import json
import time
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap
import logging
from typing import Optional, Dict, Any

class NewsImageComposer:
    """Enhanced image generator that creates news images with text summaries."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.comfyui_config = config.get('comfyui', {})
        self.server_address = self.comfyui_config.get('server_address', '127.0.0.1:8188')
        self.workflow_path = Path(self.comfyui_config.get('workflow_path', 'workflows/news_image.json'))
        self.output_dir = Path(self.comfyui_config.get('output_dir', 'output/images'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Load workflow template
        self.workflow_template = self._load_workflow()
        
    def _load_workflow(self) -> Dict[str, Any]:
        """Load the ComfyUI workflow template."""
        try:
            with open(self.workflow_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load workflow: {e}")
            return {}
    
    def generate_news_image_with_summary(self, headline: str, summary: str, style: str = "news") -> Optional[str]:
        """Generate a news image with text summary below."""
        try:
            self.logger.info(f"Generating news image with summary for: {headline[:50]}...")
            
            # Step 1: Generate the main image using ComfyUI
            main_image_path = self._generate_main_image(headline, style)
            
            if not main_image_path:
                self.logger.error("Failed to generate main image")
                return None
            
            # Step 2: Create composite image with text summary
            final_image_path = self._create_composite_with_text(main_image_path, headline, summary)
            
            # Clean up temporary main image
            if main_image_path and os.path.exists(main_image_path):
                os.remove(main_image_path)
            
            return final_image_path
            
        except Exception as e:
            self.logger.error(f"Error generating news image with summary: {e}")
            return None
    
    def _generate_main_image(self, headline: str, style: str) -> Optional[str]:
        """Generate the main image using ComfyUI."""
        try:
            # Create enhanced prompt
            prompt = self._create_enhanced_prompt(headline, style)
            negative_prompt = self.comfyui_config.get('negative_prompt', '')
            
            # Prepare workflow
            workflow = self.workflow_template.copy()
            
            # Update workflow with prompts
            workflow["6"]["inputs"]["text"] = prompt
            workflow["7"]["inputs"]["text"] = negative_prompt
            
            # Update image dimensions for main image (16:9 aspect ratio)
            workflow["5"]["inputs"]["width"] = 1024
            workflow["5"]["inputs"]["height"] = 576  # 16:9 ratio
            
            # Generate random seed
            import random
            workflow["3"]["inputs"]["seed"] = random.randint(1, 2**32 - 1)
            
            # Send to ComfyUI
            prompt_id = self._queue_prompt(workflow)
            if not prompt_id:
                return None
            
            # Wait for completion and get image
            image_data = self._wait_for_completion(prompt_id)
            if not image_data:
                return None
            
            # Save temporary main image
            temp_path = self.output_dir / f"temp_main_{int(time.time())}.png"
            with open(temp_path, 'wb') as f:
                f.write(image_data)
            
            return str(temp_path)
            
        except Exception as e:
            self.logger.error(f"Error generating main image: {e}")
            return None
    
    def _create_composite_with_text(self, main_image_path: str, headline: str, summary: str) -> Optional[str]:
        """Create composite image with main image and text summary."""
        try:
            # Load main image
            main_img = Image.open(main_image_path)
            main_width, main_height = main_img.size
            
            # Calculate composite dimensions
            text_height = 300  # Height for text area
            composite_height = main_height + text_height + 40  # 40px padding
            composite_width = max(main_width, 1024)  # Ensure minimum width
            
            # Create composite canvas
            composite = Image.new('RGB', (composite_width, composite_height), color='white')
            
            # Paste main image at top
            x_offset = (composite_width - main_width) // 2
            composite.paste(main_img, (x_offset, 20))
            
            # Add text below image
            self._add_text_to_image(composite, headline, summary, main_height + 40, composite_width)
            
            # Save final composite
            filename = self._create_filename(headline)
            final_path = self.output_dir / filename
            composite.save(final_path, 'PNG', quality=95)
            
            self.logger.info(f"Composite image saved: {final_path}")
            return str(final_path)
            
        except Exception as e:
            self.logger.error(f"Error creating composite: {e}")
            return None
    
    def _add_text_to_image(self, image: Image.Image, headline: str, summary: str, start_y: int, width: int):
        """Add formatted text to the image."""
        draw = ImageDraw.Draw(image)
        
        try:
            # Try to load a better font
            title_font = ImageFont.truetype("arial.ttf", 28)
            summary_font = ImageFont.truetype("arial.ttf", 18)
        except:
            # Fall back to default font
            title_font = ImageFont.load_default()
            summary_font = ImageFont.load_default()
        
        # Colors
        title_color = '#1a1a1a'
        summary_color = '#404040'
        
        # Text area settings
        margin = 40
        text_width = width - (margin * 2)
        
        # Draw headline
        headline_wrapped = textwrap.fill(headline, width=60)
        headline_lines = headline_wrapped.split('\n')
        
        y_pos = start_y + 20
        for line in headline_lines:
            # Center the text
            bbox = draw.textbbox((0, 0), line, font=title_font)
            text_w = bbox[2] - bbox[0]
            x_pos = (width - text_w) // 2
            
            draw.text((x_pos, y_pos), line, font=title_font, fill=title_color)
            y_pos += 35
        
        # Add separator line
        y_pos += 10
        line_start = margin
        line_end = width - margin
        draw.line([(line_start, y_pos), (line_end, y_pos)], fill='#cccccc', width=2)
        y_pos += 20
        
        # Draw summary
        summary_wrapped = textwrap.fill(summary, width=80)
        summary_lines = summary_wrapped.split('\n')
        
        for line in summary_lines:
            if y_pos > image.height - 30:  # Stop if we're near the bottom
                break
            
            # Center the text
            bbox = draw.textbbox((0, 0), line, font=summary_font)
            text_w = bbox[2] - bbox[0]
            x_pos = (width - text_w) // 2
            
            draw.text((x_pos, y_pos), line, font=summary_font, fill=summary_color)
            y_pos += 25
    
    def _create_enhanced_prompt(self, headline: str, style: str) -> str:
        """Create enhanced prompt for better image generation."""
        # Enhanced prompt templates
        templates = {
            'news': "professional news illustration of {headline}, high quality digital art, detailed, cinematic lighting, photojournalism style, editorial illustration, trending on artstation, 8k resolution, masterpiece, dramatic lighting, professional photography",
            'funny': "humorous cartoon illustration of {headline}, funny, vibrant colors, expressive characters, comedy style, playful, exaggerated expressions, digital art, high quality, detailed, meme-worthy",
            'artistic': "artistic interpretation of {headline}, modern digital art, creative composition, stylized, professional illustration, detailed brushwork, vibrant colors, masterpiece, gallery quality",
            'realistic': "photorealistic scene depicting {headline}, professional journalism photography, documentary style, high resolution, detailed, perfect lighting, award-winning photography, professional camera work"
        }
        
        template = templates.get(style.lower(), templates['news'])
        clean_headline = headline.replace('"', '').replace("'", "").strip()
        
        return template.format(headline=clean_headline)
    
    def _create_filename(self, headline: str) -> str:
        """Create a safe filename from headline."""
        import re
        safe_name = re.sub(r'[^\w\s-]', '', headline)
        safe_name = re.sub(r'\s+', '_', safe_name)
        return f"news_{safe_name[:50]}_{int(time.time())}.png"
    
    def _queue_prompt(self, workflow: Dict[str, Any]) -> Optional[str]:
        """Queue prompt to ComfyUI and return prompt ID."""
        try:
            url = f"http://{self.server_address}/prompt"
            data = {"prompt": workflow}
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get("prompt_id")
            
        except Exception as e:
            self.logger.error(f"Failed to queue prompt: {e}")
            return None
    
    def _wait_for_completion(self, prompt_id: str, timeout: int = 900) -> Optional[bytes]:
        """Wait for image generation completion and retrieve result."""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # Check if generation is complete
                    history_url = f"http://{self.server_address}/history/{prompt_id}"
                    response = requests.get(history_url, timeout=10)
                    
                    if response.status_code == 200:
                        history = response.json()
                        if prompt_id in history:
                            # Generation complete, get the image
                            outputs = history[prompt_id].get("outputs", {})
                            for node_id, output in outputs.items():
                                if "images" in output:
                                    for image_info in output["images"]:
                                        filename = image_info["filename"]
                                        subfolder = image_info.get("subfolder", "")
                                        
                                        # Download the image
                                        image_url = f"http://{self.server_address}/view"
                                        params = {"filename": filename}
                                        if subfolder:
                                            params["subfolder"] = subfolder
                                        
                                        img_response = requests.get(image_url, params=params, timeout=30)
                                        if img_response.status_code == 200:
                                            return img_response.content
                    
                    time.sleep(4)  # Check every 4 seconds
                    
                except Exception as e:
                    self.logger.error(f"Status check error: {e}")
                    time.sleep(4)
            
            self.logger.error(f"Generation timeout for prompt {prompt_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error waiting for completion: {e}")
            return None
