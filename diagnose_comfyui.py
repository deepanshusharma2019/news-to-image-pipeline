#!/usr/bin/env python3
"""
ComfyUI Diagnostic Script
Tests connection and workflow validation
"""

import requests
import json
from pathlib import Path

def test_comfyui_connection():
    """Test basic ComfyUI connection"""
    try:
        response = requests.get("http://127.0.0.1:8188/", timeout=5)
        print(f"✅ ComfyUI server connection: OK (Status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ ComfyUI server connection: FAILED - Server not running")
        return False
    except Exception as e:
        print(f"❌ ComfyUI server connection: FAILED - {e}")
        return False

def test_workflow_validation():
    """Test workflow validation"""
    workflow_path = Path("workflows/news_image.json")
    
    if not workflow_path.exists():
        print(f"❌ Workflow file missing: {workflow_path}")
        return False
    
    try:
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
        
        # Test workflow validation endpoint
        response = requests.post(
            "http://127.0.0.1:8188/prompt",
            json={"prompt": workflow, "client_id": "test"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Workflow validation: OK")
            return True
        else:
            print(f"❌ Workflow validation: FAILED")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except FileNotFoundError:
        print(f"❌ Workflow file not found: {workflow_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in workflow: {e}")
        return False
    except Exception as e:
        print(f"❌ Workflow validation error: {e}")
        return False

def check_model_files():
    """Check if required models exist"""
    model_path = Path("ComfyUI/models/checkpoints/DreamShaper_8_pruned.safetensors")
    
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"✅ DreamShaper model found: {size_mb:.1f} MB")
        return True
    else:
        print("❌ DreamShaper model missing!")
        print(f"Expected location: {model_path}")
        print("Download from: https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors")
        return False

def get_comfyui_info():
    """Get ComfyUI system info"""
    try:
        response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print("📊 ComfyUI System Info:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
        else:
            print("ℹ️  Could not retrieve system stats")
    except:
        pass

def main():
    print("🔍 ComfyUI Diagnostic Tool")
    print("=" * 40)
    
    # Test connection
    if not test_comfyui_connection():
        print("\n💡 Solution: Start ComfyUI server first:")
        print("   .\\start_comfyui.bat")
        return
    
    # Get system info
    get_comfyui_info()
    print()
    
    # Check model files
    check_model_files()
    print()
    
    # Test workflow
    test_workflow_validation()
    
    print("\n🎯 Diagnosis complete!")
    print("\nIf workflow validation failed, try:")
    print("1. Check ComfyUI console for error messages")
    print("2. Verify DreamShaper model is downloaded")
    print("3. Test with ComfyUI web interface: http://127.0.0.1:8188")

if __name__ == "__main__":
    main()
