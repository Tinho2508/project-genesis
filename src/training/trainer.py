"""Modulo de treinamento do modelo de geracao de codigo."""

import logging
from pathlib import Path
from typing import Optional

import torch
from torch.utils.data import DataLoader

logger = logging.getLogger(__name__)


class CodeTrainer:
    """Gerencia o treinamento do modelo de geracao de codigo."""

    def __init__(self, model, tokenizer, training_config):
        self.model = model
        self.tokenizer = tokenizer
        self.config = training_config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        self._setup_optimizer()
        logger.info(f"Trainer inicializado. Device: {self.device}")

    def _setup_optimizer(self):
        """Configura o otimizador AdamW."""
        from torch.optim import AdamW
        from transformers import get_linear_schedule_with_warmup

        self.optimizer = AdamW(
            self.model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
        )
        self.scheduler = None

    def train(self, train_dataset, eval_dataset=None) -> dict:
        """Executa o loop de treinamento.

        Returns:
            Dicionario com metricas do treinamento.
        """
        from transformers import get_linear_schedule_with_warmup

        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=self.config.dataloader_num_workers,
        )

        total_steps = len(train_loader) * self.config.num_epochs
        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=self.config.warmup_steps,
            num_training_steps=total_steps,
        )

        logger.info(f"Iniciando treinamento: {self.config.num_epochs} epocas, {total_steps} steps")
        history = {"train_loss": [], "eval_loss": []}

        self.model.train()
        global_step = 0

        for epoch in range(self.config.num_epochs):
            epoch_loss = 0.0
            num_batches = 0

            for batch_idx, batch in enumerate(train_loader):
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)

                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                )

                loss = outputs.loss
                loss = loss / self.config.gradient_accumulation_steps
                loss.backward()

                epoch_loss += loss.item() * self.config.gradient_accumulation_steps
                num_batches += 1

                if (batch_idx + 1) % self.config.gradient_accumulation_steps == 0:
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(),
                        self.config.max_grad_norm,
                    )
                    self.optimizer.step()
                    self.scheduler.step()
                    self.optimizer.zero_grad()
                    global_step += 1

                    if global_step % self.config.logging_steps == 0:
                        avg_loss = epoch_loss / num_batches
                        logger.info(
                            f"Epoch {epoch+1}/{self.config.num_epochs} | "
                            f"Step {global_step} | Loss: {avg_loss:.4f}"
                        )

                    if global_step % self.config.save_steps == 0:
                        self.save_checkpoint(global_step)

                    if eval_dataset and global_step % self.config.eval_steps == 0:
                        eval_loss = self.evaluate(eval_dataset)
                        history["eval_loss"].append({"step": global_step, "loss": eval_loss})
                        self.model.train()

            avg_epoch_loss = epoch_loss / max(num_batches, 1)
            history["train_loss"].append({"epoch": epoch + 1, "loss": avg_epoch_loss})
            logger.info(f"Epoch {epoch+1} concluida. Loss media: {avg_epoch_loss:.4f}")

        self.save_checkpoint(global_step, final=True)
        logger.info("Treinamento concluido!")
        return history

    def evaluate(self, eval_dataset) -> float:
        """Avalia o modelo no dataset de evaluacao."""
        eval_loader = DataLoader(
            eval_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
        )

        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in eval_loader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)

                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                )

                total_loss += outputs.loss.item()
                num_batches += 1

        avg_loss = total_loss / max(num_batches, 1)
        logger.info(f"Evaluacao - Loss: {avg_loss:.4f}")
        return avg_loss

    def save_checkpoint(self, step: int, final: bool = False) -> None:
        """Salva um checkpoint do modelo."""
        if final:
            save_dir = Path(self.config.output_dir) / "final"
        else:
            save_dir = Path(self.config.output_dir) / f"checkpoint-{step}"

        save_dir.mkdir(parents=True, exist_ok=True)

        self.model.save_pretrained(save_dir)
        self.tokenizer.save_pretrained(save_dir)

        logger.info(f"Checkpoint salvo em {save_dir}")

    @classmethod
    def from_pretrained(cls, model_path: str, training_config):
        """Carrega um modelo treinado para continuar o treinamento."""
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(model_path)
        return cls(model, tokenizer, training_config)
