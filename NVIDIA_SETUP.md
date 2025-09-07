# 🚀 NVIDIA GPU Setup Guide

This guide will help you set up the News-to-Image Automation Pipeline on your NVIDIA laptop for **10x faster image generation**.

## 📋 Prerequisites

- ✅ NVIDIA GPU with CUDA support
- ✅ Windows 10/11
- ✅ Python 3.12+ installed
- ✅ Git installed
- ✅ Repository cloned: `git clone https://github.com/deepanshusharma2019/news-to-image-pipeline.git`

## 🏃‍♂️ Quick Setup (5 Steps)

### Step 1: Navigate to Repository
```bash
cd news-to-image-pipeline
```

### Step 2: Install Python Dependencies
```bash
# Install basic requirements
pip install -r requirements.txt

# Install PyTorch with CUDA support for NVIDIA GPU
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Step 3: Download ComfyUI
```bash
# Clone ComfyUI (not included in repo due to size)
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install -r requirements.txt
cd ..
```

### Step 4: Download AI Model
```bash
# Create model directory
mkdir ComfyUI\models\checkpoints
```

**Manual Download Required:**
- Go to: https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors
- Download the file (2GB)
- Save to: `ComfyUI\models\checkpoints\DreamShaper_8_pruned.safetensors`

### Step 5: Configure for GPU
```bash
# Use GPU-optimized settings
copy config\config_gpu.yaml config\config.yaml
copy workflows\news_image_gpu.json workflows\news_image.json
```

## 🚀 Running the Pipeline

### Start ComfyUI Server
```bash
.\start_comfyui_gpu.bat
```
Wait for: "Starting server" message and "To see the GUI go to: http://127.0.0.1:8188"

### Generate Images (New Terminal)
```bash
# Single test image
python src/main.py --mode manual --verbose

# Start hourly automation
python src/main.py --mode schedule

# Custom headline
python src/main.py --headline "Your custom news headline"
```

## ⚡ GPU vs CPU Performance

| Feature | CPU Mode | GPU Mode |
|---------|----------|----------|
| Generation Time | 7-10 minutes | 30-60 seconds |
| Resolution | 768x768 | 1024x1024 |
| Steps | 35 | 50 |
| Quality | Good | Excellent |
| Sampler | Basic | Advanced |

## 🛠️ Troubleshooting

### CUDA Issues
```bash
# Check CUDA installation
python -c "import torch; print(torch.cuda.is_available())"
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

### ComfyUI Won't Start
- Check NVIDIA drivers are updated
- Ensure port 8188 is available: `netstat -an | findstr :8188`
- Try CPU mode first: `.\start_comfyui.bat`

### Memory Issues
- Reduce batch size in config
- Lower resolution (1024→768)
- Close other GPU applications

### Model Not Found
- Verify file path: `ComfyUI\models\checkpoints\DreamShaper_8_pruned.safetensors`
- Check file size: Should be ~2GB
- Re-download if corrupted

## 🎯 Expected Results

After setup, you should see:
- ComfyUI GUI at: http://127.0.0.1:8188
- Generated images in: `output\images\`
- Logs in: `output\logs\`
- GPU utilization during generation

## 📈 Optimization Tips

### For Maximum Speed
- Use GPU-only mode: `--gpu-only` in start_comfyui_gpu.bat
- Enable memory optimization: `--force-fp16`
- Close unnecessary applications

### For Best Quality
- Increase steps to 80-100 in `config\config.yaml`
- Use higher resolution: 1280x1280
- Try different samplers: `dpmpp_3m_sde_karras`

## 🆘 Support

If you encounter issues:
1. Check logs in `output\logs\`
2. Verify NVIDIA drivers
3. Test with CPU mode first
4. Check GitHub issues: https://github.com/deepanshusharma2019/news-to-image-pipeline/issues

---

**🎉 Once setup is complete, you'll have blazing-fast AI image generation from news headlines!**

Generation time: **30-60 seconds** instead of 7-10 minutes! 🚀⚡
