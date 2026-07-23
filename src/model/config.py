"""Configuracoes do modelo e treinamento para o Project Genesis."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ModelConfig:
    """Configuracao do modelo de geracao de codigo."""

    model_name: str = "microsoft/CodeGPT-small-py"
    max_length: int = 512
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 0.95
    repetition_penalty: float = 1.2
    do_sample: bool = True
    num_return_sequences: int = 1
    pad_token_id: Optional[int] = None

    def __post_init__(self):
        if self.pad_token_id is None:
            self.pad_token_id = 0


@dataclass
class TrainingConfig:
    """Configuracao do processo de treinamento."""

    output_dir: str = "outputs/models"
    log_dir: str = "outputs/logs"
    num_epochs: int = 3
    batch_size: int = 8
    learning_rate: float = 5e-5
    warmup_steps: int = 500
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    save_steps: int = 1000
    eval_steps: int = 500
    logging_steps: int = 100
    seed: int = 42
    fp16: bool = True
    gradient_accumulation_steps: int = 1
    dataloader_num_workers: int = 0

    def __post_init__(self):
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
