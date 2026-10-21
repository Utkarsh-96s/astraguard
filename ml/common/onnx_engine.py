"""ONNX export and CPU runtime inference engine with seamless PyTorch fallback."""
import contextlib
import io
import logging
import sys
import time
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import torch
from torch import nn

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(AttributeError, ValueError, io.UnsupportedOperation):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

logger = logging.getLogger(__name__)


def export_to_onnx(
    model: nn.Module,
    dummy_input: torch.Tensor,
    output_path: str | Path,
    input_names: list[str] | None = None,
    output_names: list[str] | None = None,
    dynamic_axes: dict[str, dict[int, str]] | None = None,
    opset_version: int = 18,
    dynamo: bool = False,
) -> Path:
    """Export PyTorch nn.Module to ONNX format and validate graph integrity."""
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    was_training = model.training
    model.eval()

    in_names = input_names or ["input"]
    out_names = output_names or ["output"]
    dyn_axes = dynamic_axes or {in_names[0]: {0: "batch_size"}, out_names[0]: {0: "batch_size"}}

    with torch.no_grad():
        torch.onnx.export(
            model,
            dummy_input,
            str(out_path),
            export_params=True,
            opset_version=opset_version,
            do_constant_folding=True,
            input_names=in_names,
            output_names=out_names,
            dynamic_axes=dyn_axes,
            dynamo=dynamo,
        )

    # Validate ONNX graph
    onnx_model = onnx.load(str(out_path))
    onnx.checker.check_model(onnx_model)

    if was_training:
        model.train()

    logger.info("Exported and verified ONNX model at: %s", out_path)
    return out_path


class InferenceEngine:
    """High-performance CPU inference engine using ONNX Runtime with PyTorch fallback."""

    def __init__(
        self,
        onnx_path: str | Path | None = None,
        fallback_model: nn.Module | None = None,
    ) -> None:
        self.onnx_path = Path(onnx_path) if onnx_path else None
        self.fallback_model = fallback_model
        self.session: ort.InferenceSession | None = None
        self.input_name: str = "input"
        self.output_name: str = "output"
        self.using_fallback: bool = False

        if self.fallback_model is not None:
            self.fallback_model.eval()

        self._init_session()

    def _init_session(self) -> None:
        """Initialize ONNX Runtime InferenceSession with CPU Execution Provider."""
        if self.onnx_path and self.onnx_path.exists():
            try:
                opts = ort.SessionOptions()
                opts.intra_op_num_threads = 2
                opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                self.session = ort.InferenceSession(
                    str(self.onnx_path),
                    sess_options=opts,
                    providers=["CPUExecutionProvider"],
                )
                self.input_name = self.session.get_inputs()[0].name
                self.output_name = self.session.get_outputs()[0].name
                self.using_fallback = False
                logger.info("Initialized ONNX Runtime session from %s", self.onnx_path)
                return
            except (ort.OrtExecutionError, RuntimeError, ValueError, OSError) as e:
                logger.warning("Failed to initialize ONNX session (%s). Falling back to PyTorch.", e)

        if self.fallback_model is not None:
            self.using_fallback = True
            logger.info("Using PyTorch native model fallback.")
        else:
            raise RuntimeError(
                f"Cannot initialize InferenceEngine: ONNX path '{self.onnx_path}' not found and no fallback model provided."
            )

    def predict(self, x: np.ndarray | torch.Tensor) -> np.ndarray:
        """Execute forward inference and return numpy array output."""
        if not self.using_fallback and self.session is not None:
            if isinstance(x, torch.Tensor):
                x_np = x.detach().cpu().numpy()
            else:
                x_np = np.asarray(x, dtype=np.float32)

            outputs = self.session.run([self.output_name], {self.input_name: x_np})
            return outputs[0]

        if self.fallback_model is not None:
            if isinstance(x, np.ndarray):
                x_tensor = torch.from_numpy(x).float()
            else:
                x_tensor = x.float()

            with torch.no_grad():
                out = self.fallback_model(x_tensor)
                if isinstance(out, tuple):
                    out = out[0]
                return out.detach().cpu().numpy()

        raise RuntimeError("InferenceEngine has neither active ONNX session nor fallback model.")

    def verify_parity(
        self,
        pytorch_model: nn.Module,
        dummy_input: torch.Tensor,
        tolerance: float = 1e-4,
    ) -> tuple[bool, float]:
        """Check numerical parity between PyTorch model output and ONNX runtime output."""
        pytorch_model.eval()
        with torch.no_grad():
            pt_out = pytorch_model(dummy_input)
            if isinstance(pt_out, tuple):
                pt_out = pt_out[0]
            pt_np = pt_out.detach().cpu().numpy()

        onnx_np = self.predict(dummy_input)
        max_abs_err = float(np.max(np.abs(pt_np - onnx_np)))
        is_close = max_abs_err <= tolerance
        return is_close, max_abs_err

    def measure_latency(
        self,
        dummy_input: np.ndarray | torch.Tensor,
        warmups: int = 10,
        iterations: int = 100,
    ) -> dict[str, float]:
        """Benchmark inference latency (p50, p95, p99, mean) in milliseconds."""
        # Warmup
        for _ in range(warmups):
            self.predict(dummy_input)

        latencies_ms: list[float] = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            self.predict(dummy_input)
            t1 = time.perf_counter()
            latencies_ms.append((t1 - t0) * 1000.0)

        latencies_arr = np.array(latencies_ms)
        return {
            "p50": round(float(np.percentile(latencies_arr, 50)), 3),
            "p95": round(float(np.percentile(latencies_arr, 95)), 3),
            "p99": round(float(np.percentile(latencies_arr, 99)), 3),
            "mean": round(float(np.mean(latencies_arr)), 3),
            "min": round(float(np.min(latencies_arr)), 3),
            "max": round(float(np.max(latencies_arr)), 3),
        }
