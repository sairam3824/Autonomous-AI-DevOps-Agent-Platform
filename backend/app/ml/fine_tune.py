"""
CodeLlama Fine-Tuning Scaffold for YAML Generation

This module provides a starting point for fine-tuning CodeLlama on DevOps YAML
generation tasks. It uses PyTorch with a simple training loop.

NOTE: This is a scaffold. For production fine-tuning, you would need:
- A proper dataset of YAML examples (1000+ samples)
- GPU resources (A100 or better recommended)
- LoRA/QLoRA for efficient fine-tuning
- Proper evaluation metrics
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from app.core.logging import get_logger

logger = get_logger(__name__)


SAMPLE_TRAINING_DATA = [
    {
        "input": "Generate a GitHub Actions workflow for a Node.js app with tests",
        "output": """name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm test""",
    },
    {
        "input": "Generate a Docker Compose for Python app with PostgreSQL",
        "output": """version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/app
    depends_on:
      - db
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: app
      POSTGRES_PASSWORD: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:""",
    },
    {
        "input": "Generate a Kubernetes deployment for a web app with 3 replicas",
        "output": """apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
        - name: web-app
          image: web-app:latest
          ports:
            - containerPort: 8080
          resources:
            requests:
              memory: 128Mi
              cpu: 100m
            limits:
              memory: 256Mi
              cpu: 200m""",
    },
]


class YAMLDataset(Dataset):
    def __init__(self, data: list[dict[str, str]], max_length: int = 512) -> None:
        self.data = data
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        item = self.data[idx]
        input_text = item["input"]
        output_text = item["output"]

        input_ids = self._simple_tokenize(input_text)
        labels = self._simple_tokenize(output_text)

        return {
            "input_ids": input_ids,
            "attention_mask": torch.ones_like(input_ids),
            "labels": labels,
        }

    def _simple_tokenize(self, text: str) -> torch.Tensor:
        tokens = [ord(c) % 32000 for c in text[: self.max_length]]
        padding = [0] * (self.max_length - len(tokens))
        return torch.tensor(tokens + padding, dtype=torch.long)


class SimpleTransformerBlock(nn.Module):
    def __init__(self, embed_dim: int = 256, num_heads: int = 4, ff_dim: int = 512) -> None:
        super().__init__()
        self.attention = nn.MultiheadAttention(embed_dim, num_heads, batch_first=True)
        self.norm1 = nn.LayerNorm(embed_dim)
        self.ff = nn.Sequential(
            nn.Linear(embed_dim, ff_dim),
            nn.GELU(),
            nn.Linear(ff_dim, embed_dim),
        )
        self.norm2 = nn.LayerNorm(embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        attn_out, _ = self.attention(x, x, x)
        x = self.norm1(x + attn_out)
        ff_out = self.ff(x)
        x = self.norm2(x + ff_out)
        return x


class YAMLGeneratorModel(nn.Module):
    def __init__(
        self,
        vocab_size: int = 32000,
        embed_dim: int = 256,
        num_heads: int = 4,
        num_layers: int = 4,
        max_length: int = 512,
    ) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.position = nn.Embedding(max_length, embed_dim)
        self.blocks = nn.ModuleList(
            [SimpleTransformerBlock(embed_dim, num_heads) for _ in range(num_layers)]
        )
        self.head = nn.Linear(embed_dim, vocab_size)

    def forward(self, input_ids: torch.Tensor, **kwargs) -> torch.Tensor:
        batch_size, seq_len = input_ids.shape
        positions = torch.arange(seq_len, device=input_ids.device).unsqueeze(0).expand(batch_size, -1)
        x = self.embedding(input_ids) + self.position(positions)
        for block in self.blocks:
            x = block(x)
        logits = self.head(x)
        return logits


@dataclass
class FineTuneConfig:
    epochs: int = 3
    batch_size: int = 2
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    max_length: int = 512
    warmup_steps: int = 100
    save_path: str = "./fine_tuned_model"
    device: str = "cpu"


class CodeLlamaFineTuner:
    def __init__(self, config: FineTuneConfig | None = None) -> None:
        self.config = config or FineTuneConfig()
        self.model = YAMLGeneratorModel(max_length=self.config.max_length)
        self.model.to(self.config.device)
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
        )
        self.loss_fn = nn.CrossEntropyLoss(ignore_index=0)

    def prepare_data(self, data: list[dict[str, str]] | None = None) -> DataLoader:
        dataset = YAMLDataset(data or SAMPLE_TRAINING_DATA, max_length=self.config.max_length)
        return DataLoader(dataset, batch_size=self.config.batch_size, shuffle=True)

    def train_epoch(self, dataloader: DataLoader) -> float:
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch in dataloader:
            input_ids = batch["input_ids"].to(self.config.device)
            labels = batch["labels"].to(self.config.device)

            logits = self.model(input_ids)
            loss = self.loss_fn(logits.view(-1, logits.size(-1)), labels.view(-1))

            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / max(num_batches, 1)
        return avg_loss

    def evaluate(self, dataloader: DataLoader) -> dict[str, float]:
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch["input_ids"].to(self.config.device)
                labels = batch["labels"].to(self.config.device)

                logits = self.model(input_ids)
                loss = self.loss_fn(logits.view(-1, logits.size(-1)), labels.view(-1))

                total_loss += loss.item()
                num_batches += 1

        avg_loss = total_loss / max(num_batches, 1)
        perplexity = torch.exp(torch.tensor(avg_loss)).item()

        return {"eval_loss": avg_loss, "perplexity": perplexity}

    def train(self, data: list[dict[str, str]] | None = None) -> list[dict[str, Any]]:
        logger.info("fine_tune_started", epochs=self.config.epochs)
        dataloader = self.prepare_data(data)
        history: list[dict[str, Any]] = []

        for epoch in range(self.config.epochs):
            train_loss = self.train_epoch(dataloader)
            eval_metrics = self.evaluate(dataloader)

            record = {
                "epoch": epoch + 1,
                "train_loss": round(train_loss, 4),
                **{k: round(v, 4) for k, v in eval_metrics.items()},
            }
            history.append(record)
            logger.info("fine_tune_epoch", **record)

        self.save_model()
        logger.info("fine_tune_completed", total_epochs=self.config.epochs)
        return history

    def save_model(self) -> None:
        save_path = Path(self.config.save_path)
        save_path.mkdir(parents=True, exist_ok=True)
        torch.save(self.model.state_dict(), save_path / "model.pt")
        with open(save_path / "config.json", "w") as f:
            json.dump({"max_length": self.config.max_length, "epochs": self.config.epochs}, f)
        logger.info("model_saved", path=str(save_path))

    def load_model(self, path: str) -> None:
        self.model.load_state_dict(torch.load(Path(path) / "model.pt", weights_only=True))
        logger.info("model_loaded", path=path)
