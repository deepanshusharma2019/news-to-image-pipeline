#!/bin/bash
echo "Starting News to Image Automation Pipeline"
echo

echo "Checking if ComfyUI is running..."
sleep 2

echo "Starting the news-to-image pipeline..."
echo

# Run the pipeline in scheduled mode
python src/main.py --mode schedule --verbose
