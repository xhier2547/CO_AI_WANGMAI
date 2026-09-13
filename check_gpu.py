import torch
import platform
import subprocess

print("========== GPU CHECK REPORT ==========")
print(f"Python version : {platform.python_version()}")
print(f"Torch version  : {torch.__version__}")
print(f"CUDA available : {torch.cuda.is_available()}")
print(f"CUDA version   : {torch.version.cuda}")
print(f"Device count   : {torch.cuda.device_count()}")

if torch.cuda.is_available():
    print(f"GPU Name       : {torch.cuda.get_device_name(0)}")
else:
    print("⚠️  Torch ไม่เห็น GPU (กำลังใช้ CPU เท่านั้น)")
    print("\nลองรันคำสั่งนี้ใน PowerShell เพื่อตรวจจาก driver โดยตรง:")
    print("nvidia-smi\n")

# optional: check with system command
try:
    print("\n========== NVIDIA-SMI OUTPUT ==========")
    output = subprocess.check_output("nvidia-smi", shell=True, text=True)
    print(output)
except Exception as e:
    print("ไม่พบคำสั่ง nvidia-smi หรือไม่ได้ติดตั้ง NVIDIA driver:", e)
