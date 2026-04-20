"""
RLHF (Reinforcement Learning from Human Feedback) Scaffold

Basic reward model + PPO training loop for agent decision optimization.
This is a scaffold demonstrating the RLHF pipeline structure.

For production use, you would need:
- A large dataset of human preference comparisons
- GPU resources
- Integration with the actual agent policy model
- Proper KL divergence penalty tuning
"""

from dataclasses import dataclass
from typing import Any

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from app.core.logging import get_logger

logger = get_logger(__name__)


SAMPLE_PREFERENCE_DATA = [
    {
        "prompt": "Fix CrashLoopBackOff error",
        "chosen": "Check pod logs with kubectl logs, verify resource limits, check liveness probes",
        "rejected": "Delete and recreate the pod",
    },
    {
        "prompt": "Optimize CI/CD pipeline",
        "chosen": "Add dependency caching, parallel test jobs, artifact upload, and concurrency controls",
        "rejected": "Just run everything sequentially",
    },
    {
        "prompt": "Generate Docker Compose for microservices",
        "chosen": "Use health checks, named volumes, resource limits, proper networking, and restart policies",
        "rejected": "Put all services with minimal config",
    },
]


class PreferenceDataset(Dataset):
    def __init__(self, data: list[dict[str, str]], max_length: int = 256) -> None:
        self.data = data
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        item = self.data[idx]
        prompt_ids = self._tokenize(item["prompt"])
        chosen_ids = self._tokenize(item["chosen"])
        rejected_ids = self._tokenize(item["rejected"])
        return {
            "prompt_ids": prompt_ids,
            "chosen_ids": chosen_ids,
            "rejected_ids": rejected_ids,
        }

    def _tokenize(self, text: str) -> torch.Tensor:
        tokens = [ord(c) % 10000 for c in text[: self.max_length]]
        padding = [0] * (self.max_length - len(tokens))
        return torch.tensor(tokens + padding, dtype=torch.long)


class RewardModel(nn.Module):
    def __init__(self, vocab_size: int = 10000, embed_dim: int = 128, hidden_dim: int = 256) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.encoder = nn.Sequential(
            nn.Linear(embed_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
        )
        self.reward_head = nn.Linear(hidden_dim, 1)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        x = self.embedding(input_ids)
        mask = (input_ids != 0).float().unsqueeze(-1)
        x = (x * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        x = self.encoder(x)
        reward = self.reward_head(x)
        return reward.squeeze(-1)


class SimplePolicy(nn.Module):
    def __init__(self, vocab_size: int = 10000, embed_dim: int = 128, hidden_dim: int = 256) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.encoder = nn.Sequential(
            nn.Linear(embed_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        self.value_head = nn.Linear(hidden_dim, 1)
        self.action_head = nn.Linear(hidden_dim, vocab_size)

    def forward(self, input_ids: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        x = self.embedding(input_ids)
        mask = (input_ids != 0).float().unsqueeze(-1)
        x = (x * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        x = self.encoder(x)
        values = self.value_head(x).squeeze(-1)
        action_logits = self.action_head(x)
        return action_logits, values


@dataclass
class PPOConfig:
    epochs: int = 3
    batch_size: int = 2
    reward_lr: float = 1e-4
    policy_lr: float = 1e-5
    clip_epsilon: float = 0.2
    kl_penalty: float = 0.01
    gamma: float = 0.99
    device: str = "cpu"


class PPOTrainer:
    def __init__(self, config: PPOConfig | None = None) -> None:
        self.config = config or PPOConfig()
        self.reward_model = RewardModel()
        self.policy = SimplePolicy()
        self.ref_policy = SimplePolicy()

        self.reward_model.to(self.config.device)
        self.policy.to(self.config.device)
        self.ref_policy.to(self.config.device)

        self.ref_policy.load_state_dict(self.policy.state_dict())

        self.reward_optimizer = torch.optim.Adam(
            self.reward_model.parameters(), lr=self.config.reward_lr
        )
        self.policy_optimizer = torch.optim.Adam(
            self.policy.parameters(), lr=self.config.policy_lr
        )

    def train_reward_model(self, data: list[dict[str, str]] | None = None) -> list[dict[str, float]]:
        logger.info("reward_model_training_started")
        dataset = PreferenceDataset(data or SAMPLE_PREFERENCE_DATA)
        dataloader = DataLoader(dataset, batch_size=self.config.batch_size, shuffle=True)
        history: list[dict[str, float]] = []

        for epoch in range(self.config.epochs):
            total_loss = 0.0
            total_acc = 0.0
            num_batches = 0

            for batch in dataloader:
                chosen_ids = batch["chosen_ids"].to(self.config.device)
                rejected_ids = batch["rejected_ids"].to(self.config.device)

                chosen_rewards = self.reward_model(chosen_ids)
                rejected_rewards = self.reward_model(rejected_ids)

                loss = -torch.log(torch.sigmoid(chosen_rewards - rejected_rewards)).mean()

                self.reward_optimizer.zero_grad()
                loss.backward()
                self.reward_optimizer.step()

                acc = (chosen_rewards > rejected_rewards).float().mean().item()
                total_loss += loss.item()
                total_acc += acc
                num_batches += 1

            record = {
                "epoch": epoch + 1,
                "reward_loss": round(total_loss / max(num_batches, 1), 4),
                "accuracy": round(total_acc / max(num_batches, 1), 4),
            }
            history.append(record)
            logger.info("reward_model_epoch", **record)

        return history

    def compute_rewards(self, response_ids: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            rewards = self.reward_model(response_ids)
        return rewards

    def ppo_step(self, prompt_ids: torch.Tensor, response_ids: torch.Tensor) -> dict[str, float]:
        rewards = self.compute_rewards(response_ids)

        action_logits, values = self.policy(prompt_ids)
        with torch.no_grad():
            ref_logits, _ = self.ref_policy(prompt_ids)

        log_probs = torch.log_softmax(action_logits, dim=-1)
        ref_log_probs = torch.log_softmax(ref_logits, dim=-1)

        kl_div = (torch.exp(log_probs) * (log_probs - ref_log_probs)).sum(dim=-1).mean()

        advantages = rewards - values.detach()
        policy_loss = -(advantages * log_probs.mean(dim=-1)).mean()
        value_loss = nn.functional.mse_loss(values, rewards)
        total_loss = policy_loss + 0.5 * value_loss + self.config.kl_penalty * kl_div

        self.policy_optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy.parameters(), 1.0)
        self.policy_optimizer.step()

        return {
            "policy_loss": policy_loss.item(),
            "value_loss": value_loss.item(),
            "kl_divergence": kl_div.item(),
            "mean_reward": rewards.mean().item(),
            "total_loss": total_loss.item(),
        }

    def train(self, data: list[dict[str, str]] | None = None) -> dict[str, Any]:
        logger.info("ppo_training_started")

        reward_history = self.train_reward_model(data)

        dataset = PreferenceDataset(data or SAMPLE_PREFERENCE_DATA)
        dataloader = DataLoader(dataset, batch_size=self.config.batch_size, shuffle=True)
        ppo_history: list[dict[str, Any]] = []

        for epoch in range(self.config.epochs):
            epoch_metrics: dict[str, float] = {}
            num_batches = 0

            for batch in dataloader:
                prompt_ids = batch["prompt_ids"].to(self.config.device)
                chosen_ids = batch["chosen_ids"].to(self.config.device)

                metrics = self.ppo_step(prompt_ids, chosen_ids)

                for k, v in metrics.items():
                    epoch_metrics[k] = epoch_metrics.get(k, 0.0) + v
                num_batches += 1

            avg_metrics = {k: round(v / max(num_batches, 1), 4) for k, v in epoch_metrics.items()}
            avg_metrics["epoch"] = epoch + 1
            ppo_history.append(avg_metrics)
            logger.info("ppo_epoch", **avg_metrics)

        logger.info("ppo_training_completed")
        return {
            "reward_training": reward_history,
            "ppo_training": ppo_history,
        }
