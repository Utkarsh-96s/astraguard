"""Config-driven PyTorch trainer for ASTRA-GUARD deep learning models."""
import contextlib
import io
import sys

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(AttributeError, ValueError, io.UnsupportedOperation):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

import argparse
import csv
import json
import logging
import os
import random
from pathlib import Path
from typing import Any

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import yaml
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from ml.common.dummy_model import DummySequenceModel
from ml.common.onnx_engine import InferenceEngine, export_to_onnx
from ml.common.registry import (
    ModelRegistryEntry,
    compute_data_hash,
    extract_param_counts,
    register_model,
)
from ml.health.lstm_ae import LSTMAutoencoderNet
from ml.health.tcn_ae import TCNAutoencoderNet
from ml.health.transformer_ae import TransformerAutoencoderNet
from ml.reports.figure_helper import apply_style, save_figure

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def set_seed(seed: int = 42) -> None:
    """Enforce deterministic random seeds across libraries."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    # Ensure deterministic algorithms where supported
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def generate_synthetic_dataset(
    num_samples: int,
    seq_len: int,
    in_channels: int,
    seed: int = 42,
) -> tuple[torch.Tensor, str]:
    """Generate reproducible harmonic sequence data for training/validation."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 4 * np.pi, seq_len)
    data = np.zeros((num_samples, seq_len, in_channels), dtype=np.float32)

    for i in range(num_samples):
        for c in range(in_channels):
            freq = 0.5 + 0.5 * c + rng.uniform(-0.05, 0.05)
            phase = rng.uniform(0, 2 * np.pi)
            noise = rng.normal(0, 0.05, seq_len)
            data[i, :, c] = np.sin(freq * t + phase) + noise

    data_bytes = data.tobytes()
    data_hash = compute_data_hash(data_bytes)
    return torch.from_numpy(data), data_hash


class EarlyStopping:
    """Early stopping monitor based on validation loss."""

    def __init__(self, patience: int = 4, min_delta: float = 1e-4) -> None:
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = float("inf")
        self.early_stop = False

    def __call__(self, val_loss: float) -> bool:
        if val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter = 0
            return True  # Improved
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
            return False


def plot_loss_curve(
    train_losses: list[float],
    val_losses: list[float],
    model_id: str,
    model_version: str,
    dataset_name: str,
    data_hash: str,
) -> dict[str, Any]:
    """Plot SpaceX-style monochrome training curve and save to figures/manifest."""
    apply_style()
    fig, ax = plt.subplots(figsize=(8, 4.5))

    epochs = list(range(1, len(train_losses) + 1))
    ax.plot(epochs, train_losses, linestyle="-", marker="o", label="Training Loss (MSE)", color="#f0f0fa")
    ax.plot(epochs, val_losses, linestyle="--", marker="s", label="Validation Loss (MSE)", color="#c4c4cf")

    ax.set_title(f"{model_id} // LOSS CONVERGENCE PROFILE", pad=12)
    ax.set_xlabel("EPOCH")
    ax.set_ylabel("MEAN SQUARED ERROR (MSE)")
    ax.legend(loc="upper right")
    ax.grid(True)

    figure_id = f"FIG-{model_id}-LOSS"
    title = f"{model_id} Loss Convergence"
    desc = f"Epoch-wise MSE convergence profile for {model_id} v{model_version} on {dataset_name}."

    entry = save_figure(
        fig=fig,
        figure_id=figure_id,
        title=title,
        description=desc,
        model_version=model_version,
        dataset=dataset_name,
        data_hash=data_hash,
        tags=["loss_curve", "convergence", "training"],
    )
    plt.close(fig)
    return entry


def train_model(config_path: str | Path, fast: bool = False) -> dict[str, Any]:
    """Execute training pipeline according to declarative YAML configuration."""
    cfg_path = Path(config_path)
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    seed = cfg.get("seed", 42)
    set_seed(seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = cfg.get("training", {}).get("use_amp", False) and torch.cuda.is_available()

    # Determine parameters based on fast mode
    train_cfg = cfg.get("training", {})
    epochs = train_cfg.get("epochs_fast", 3) if fast else train_cfg.get("epochs", 10)
    batch_size = train_cfg.get("batch_size", 16)
    lr = train_cfg.get("lr", 0.005)
    weight_decay = train_cfg.get("weight_decay", 1e-4)
    patience = train_cfg.get("patience", 4)

    ds_cfg = cfg.get("dataset", {})
    num_samples = ds_cfg.get("num_samples_fast", 40) if fast else ds_cfg.get("num_samples", 200)
    in_channels = ds_cfg.get("in_channels", 4)
    seq_len = ds_cfg.get("seq_len", 32)
    dataset_name = ds_cfg.get("name", "synthetic_dataset")

    # Generate or load data
    raw_tensor, data_hash = generate_synthetic_dataset(
        num_samples=num_samples,
        seq_len=seq_len,
        in_channels=in_channels,
        seed=seed,
    )

    # Train / Val Split (80 / 20)
    split_idx = int(0.8 * num_samples)
    train_x = raw_tensor[:split_idx]
    val_x = raw_tensor[split_idx:]

    train_loader = DataLoader(TensorDataset(train_x), batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(TensorDataset(val_x), batch_size=batch_size, shuffle=False)

    # Model instantiation
    arch_name = cfg.get("architecture", "DummySequenceModel")
    m_cfg = cfg.get("model", {})
    hidden_dim = m_cfg.get("hidden_dim", 32)
    latent_dim = m_cfg.get("latent_dim", 16)

    if arch_name == "DummySequenceModel":
        model = DummySequenceModel(in_channels=in_channels, seq_len=seq_len).to(device)
    elif arch_name in ("LSTMAutoencoderNet", "LSTMAutoencoder"):
        model = LSTMAutoencoderNet(input_dim=in_channels, hidden_dim=hidden_dim, latent_dim=latent_dim).to(device)
    elif arch_name in ("TCNAutoencoderNet", "TCNAutoencoder"):
        dilations = tuple(m_cfg.get("dilations", [1, 2, 4, 8]))
        model = TCNAutoencoderNet(
            input_dim=in_channels,
            hidden_dim=hidden_dim,
            latent_dim=latent_dim,
            dilations=dilations,
        ).to(device)
    elif arch_name in ("TransformerAutoencoderNet", "TransformerAutoencoder"):
        d_model = m_cfg.get("d_model", 32)
        nhead = m_cfg.get("nhead", 4)
        num_layers = m_cfg.get("num_layers", 2)
        model = TransformerAutoencoderNet(
            input_dim=in_channels,
            d_model=d_model,
            nhead=nhead,
            num_layers=num_layers,
            latent_dim=latent_dim,
            max_len=max(256, seq_len * 2),
        ).to(device)
    else:
        raise ValueError(f"Unknown architecture: {arch_name}")

    criterion = nn.MSELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    early_stopping = EarlyStopping(patience=patience)
    scaler = torch.cuda.amp.GradScaler() if use_amp else None

    # Output directory
    out_dir = Path(cfg.get("export", {}).get("output_dir", "ml/artifacts/model_run"))
    out_dir.mkdir(parents=True, exist_ok=True)
    best_ckpt_path = out_dir / "best_model.pt"
    last_ckpt_path = out_dir / "last_model.pt"
    log_csv_path = out_dir / "training_log.csv"
    log_json_path = out_dir / "training_log.json"

    train_losses: list[float] = []
    val_losses: list[float] = []
    epoch_logs: list[dict[str, Any]] = []

    logger.info("Starting training %s for %d epochs (fast=%s, device=%s, amp=%s)", cfg["model_id"], epochs, fast, device, use_amp)

    for epoch in range(1, epochs + 1):
        model.train()
        running_train_loss = 0.0

        for (batch_x,) in train_loader:
            batch_x = batch_x.to(device)
            optimizer.zero_grad()

            if use_amp and scaler is not None:
                with torch.cuda.amp.autocast():
                    pred = model(batch_x)
                    loss = criterion(pred, batch_x)
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:
                pred = model(batch_x)
                loss = criterion(pred, batch_x)
                loss.backward()
                optimizer.step()

            running_train_loss += loss.item() * len(batch_x)

        epoch_train_loss = running_train_loss / len(train_x)

        # Validation
        model.eval()
        running_val_loss = 0.0
        with torch.no_grad():
            for (batch_x,) in val_loader:
                batch_x = batch_x.to(device)
                pred = model(batch_x)
                loss = criterion(pred, batch_x)
                running_val_loss += loss.item() * len(batch_x)

        epoch_val_loss = running_val_loss / len(val_x)

        train_losses.append(epoch_train_loss)
        val_losses.append(epoch_val_loss)

        epoch_record = {
            "epoch": epoch,
            "train_loss": round(epoch_train_loss, 6),
            "val_loss": round(epoch_val_loss, 6),
        }
        epoch_logs.append(epoch_record)
        logger.info("Epoch %02d/%02d — train_loss: %.6f, val_loss: %.6f", epoch, epochs, epoch_train_loss, epoch_val_loss)

        # Checkpointing
        torch.save(model.state_dict(), last_ckpt_path)
        if early_stopping(epoch_val_loss):
            torch.save(model.state_dict(), best_ckpt_path)
            logger.info("Saved new best checkpoint to %s", best_ckpt_path)

        if early_stopping.early_stop:
            logger.info("Early stopping triggered at epoch %d", epoch)
            break

    # Save CSV and JSON training logs
    with open(log_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["epoch", "train_loss", "val_loss"])
        writer.writeheader()
        writer.writerows(epoch_logs)

    with open(log_json_path, "w", encoding="utf-8") as f:
        json.dump({"model_id": cfg["model_id"], "epochs": epoch_logs}, f, indent=2)

    # Load best weights for export
    if best_ckpt_path.exists():
        model.load_state_dict(torch.load(best_ckpt_path, map_location="cpu"))
    model = model.to("cpu")
    model.eval()

    # Extract param counts
    dummy_input = torch.zeros((1, seq_len, in_channels), dtype=torch.float32)
    param_counts = extract_param_counts(model, input_data=dummy_input)

    # ONNX Export
    onnx_path = None
    latency_stats: dict[str, float] = {}
    if cfg.get("export", {}).get("onnx", True):
        onnx_file = out_dir / f"{cfg['model_id']}.onnx"
        export_to_onnx(
            model=model,
            dummy_input=dummy_input,
            output_path=onnx_file,
            input_names=["telemetry_sequence"],
            output_names=["reconstructed_sequence"],
            dynamic_axes={
                "telemetry_sequence": {0: "batch_size"},
                "reconstructed_sequence": {0: "batch_size"},
            },
        )
        onnx_path = str(onnx_file.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")

        # Benchmark ONNX Inference Engine and verify parity
        engine = InferenceEngine(onnx_path=onnx_file, fallback_model=model)
        is_close, max_diff = engine.verify_parity(model, dummy_input)
        logger.info("ONNX parity check: is_close=%s, max_abs_diff=%.2e", is_close, max_diff)

        latency_stats = engine.measure_latency(dummy_input, warmups=10, iterations=100)
        logger.info("Measured latency (CPU): p50=%.3f ms, p95=%.3f ms", latency_stats["p50"], latency_stats["p95"])

    # Generate monochrome loss curve figure
    figure_entry = plot_loss_curve(
        train_losses=train_losses,
        val_losses=val_losses,
        model_id=cfg["model_id"],
        model_version=cfg["version"],
        dataset_name=dataset_name,
        data_hash=data_hash,
    )

    # Register in Model Registry
    registry_entry = ModelRegistryEntry(
        model_id=cfg["model_id"],
        name=cfg["name"],
        version=cfg["version"],
        architecture=arch_name,
        subsystem=cfg.get("subsystem", "foundation"),
        data_hash=data_hash,
        params_count=param_counts,
        config=cfg,
        metrics={
            "final_train_loss": round(train_losses[-1], 6),
            "final_val_loss": round(val_losses[-1], 6),
            "best_val_loss": round(min(val_losses), 6),
        },
        latency_ms=latency_stats,
        onnx_path=onnx_path,
        checkpoint_path=str(best_ckpt_path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/"),
        training_log_path=str(log_json_path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/"),
        limitations=cfg.get("limitations", []),
    )
    registered_record = register_model(registry_entry)

    logger.info("Stage A Training Run Completed for %s", cfg["model_id"])
    return {
        "model_id": cfg["model_id"],
        "registry": registered_record,
        "figure": figure_entry,
        "onnx_path": onnx_path,
        "best_val_loss": min(val_losses),
        "latency_ms": latency_stats,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="ASTRA-GUARD Deep Learning Model Trainer")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML training configuration")
    parser.add_argument("--fast", action="store_true", help="Run rapid CI verification with truncated epochs/dataset")
    args = parser.parse_args()

    train_model(config_path=args.config, fast=args.fast)


if __name__ == "__main__":
    main()
