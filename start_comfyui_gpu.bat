@echo off
title ComfyUI GPU Server
echo ======================================
echo    ComfyUI GPU-Optimized Server
echo ======================================
echo.
echo Starting ComfyUI with GPU optimizations...
echo Server will be available at: http://127.0.0.1:8188
echo.

cd ComfyUI

REM GPU-optimized arguments
python main.py --listen 0.0.0.0 --port 8188 --gpu-only --disable-smart-memory --force-fp16

pause
