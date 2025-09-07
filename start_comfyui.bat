@echo off
echo Starting ComfyUI Server...
echo.
echo ComfyUI will run on: http://127.0.0.1:8188
echo Press Ctrl+C to stop the server
echo.

cd /d "ComfyUI"
python main.py --cpu --listen 127.0.0.1 --port 8188

pause
