@echo off
echo Starting News to Image Automation Pipeline
echo.

echo Checking if ComfyUI is running...
timeout /t 2 > nul

echo Starting the news-to-image pipeline...
echo.

REM Run the pipeline in scheduled mode
C:\Users\Dipanshu\AppData\Local\Microsoft\WindowsApps\python.exe src/main.py --mode schedule --verbose

pause
