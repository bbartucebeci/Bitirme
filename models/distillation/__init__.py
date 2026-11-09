"""PULSAR Knowledge Distillation and FPGA Compact Student Module.

Contains:
- CompactGRUStudent: 2-layer GRU (<32k weights, 31.5 KB INT8)
- CompactTCNStudent: Causal dilated TCN (<17k weights, 16.2 KB INT8)
- distill_trainer: Supervised + KD distillation trainer with dynamic INT8 quantization
"""

from .student_models import CompactGRUStudent, CompactTCNStudent
from .distill_trainer import train_student_model, evaluate_student

__all__ = [
    "CompactGRUStudent",
    "CompactTCNStudent",
    "train_student_model",
    "evaluate_student",
]
