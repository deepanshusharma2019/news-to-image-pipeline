#!/usr/bin/env python3
"""
Test script to demonstrate news image composition with text summary.
Uses existing generated images to create composite images with text.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

from summary_generator import SummaryGenerator
from PIL import Image, ImageDraw, ImageFont
import textwrap

def create_demo_composite():
    """Create a demo composite image with text summary."""
    
    # Check if we have any generated images
    comfyui_output = Path("ComfyUI/output")
    png_files = list(comfyui_output.glob("ComfyUI_*.png"))
    
    if not png_files:
        print("No generated images found in ComfyUI/output/")
        return
    
    # Use the most recent image
    latest_image = max(png_files, key=lambda p: p.stat().st_mtime)
    print(f"Using image: {latest_image}")
    
    # Create a demo headline and summary
    demo_headline = "More than 425 arrested at rally against Palestine Action ban in London"
    
    # Generate summary
    summary_gen = SummaryGenerator()
    summary = summary_gen.generate_summary(demo_headline)
    
    print(f"Headline: {demo_headline}")
    print(f"Summary: {summary}")
    
    # Create composite
    create_composite_image(str(latest_image), demo_headline, summary)

def create_composite_image(image_path: str, headline: str, summary: str):
    """Create composite image with main image and text summary."""
    try:
        # Load main image
        main_img = Image.open(image_path)
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
        add_text_to_image(composite, headline, summary, main_height + 40, composite_width)
        
        # Save final composite
        output_path = Path("output/images") / f"demo_composite_{int(__import__('time').time())}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        composite.save(output_path, 'PNG', quality=95)
        
        print(f"Demo composite saved: {output_path}")
        return str(output_path)
        
    except Exception as e:
        print(f"Error creating composite: {e}")
        return None

def add_text_to_image(image: Image.Image, headline: str, summary: str, start_y: int, width: int):
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

if __name__ == "__main__":
    create_demo_composite()
