# torch_safe.py
import torch
import ultralytics.nn.tasks as tasks
import torch.nn.modules.container as container
import torch.nn.modules.conv as conv
import torch.nn.modules.upsampling as upsampling
import torch.nn.modules.batchnorm as batchnorm
import torch.nn.modules.activation as activation

# allowlist modules ที่ YOLO ใช้บ่อย
torch.serialization.add_safe_globals([
    tasks.DetectionModel,
    container.Sequential,
    conv.Conv2d,
    upsampling.Upsample,
    batchnorm.BatchNorm2d,
    activation.SiLU,
])
