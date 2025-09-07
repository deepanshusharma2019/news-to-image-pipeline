# News-to-Image Automation Pipeline

This project automatically fetches news headlines every hour and generates images using ComfyUI and Stable Diffusion.

## Project Structure
- `src/` - Main source code
- `config/` - Configuration files
- `workflows/` - ComfyUI workflow files
- `output/` - Generated images and logs
- `requirements.txt` - Python dependencies

## Key Features
- Automated news fetching from multiple sources
- Image generation using ComfyUI API
- Scheduled execution every hour
- Configurable prompts and styles
- Image archiving and management

## Setup Instructions
1. Install Python dependencies
2. Configure API keys in config files
3. Set up ComfyUI server
4. Run the automation script

## Technologies Used
- Python for automation and scheduling
- ComfyUI API for image generation
- News APIs for content fetching
- APScheduler for task scheduling
