"""Classical image processing and radar differencing baselines for flood segmentation."""

import numpy as np


class OtsuThresholdBaseline:
    """Otsu automatic thresholding baseline on single-date SAR backscatter chips.

    Computes the bimodal intensity threshold that maximizes between-class variance.
    Radar water pixels have low backscatter due to specular reflection.
    """

    def __init__(self) -> None:
        self.fitted_threshold: float = 0.0
        self.is_fitted: bool = False

    @staticmethod
    def _compute_otsu_threshold(image: np.ndarray) -> float:
        """Calculate optimal Otsu threshold for a 2D float or uint8 image."""
        flat = image.ravel()
        # Scale to 0..255 integer bin space
        min_v, max_v = float(np.min(flat)), float(np.max(flat))
        if max_v - min_v < 1e-6:
            return min_v

        scaled = ((flat - min_v) / (max_v - min_v) * 255.0).astype(np.uint8)
        hist, _ = np.histogram(scaled, bins=256, range=(0, 256))
        total_pixels = flat.size

        current_max: float = 0.0
        best_t: int = 128
        weight_bg: float = 0.0
        sum_bg: float = 0.0
        sum_total: float = float(np.dot(np.arange(256), hist))

        for t in range(256):
            weight_bg += hist[t]
            if weight_bg == 0:
                continue
            weight_fg = total_pixels - weight_bg
            if weight_fg == 0:
                break

            sum_bg += t * hist[t]
            mean_bg = sum_bg / weight_bg
            mean_fg = (sum_total - sum_bg) / weight_fg

            # Between-class variance
            var_between = weight_bg * weight_fg * ((mean_bg - mean_fg) ** 2)
            if var_between > current_max:
                current_max = var_between
                best_t = t

        return min_v + (best_t / 255.0) * (max_v - min_v)

    def fit(self, images: np.ndarray) -> "OtsuThresholdBaseline":
        """Compute average Otsu threshold over training chips."""
        thresholds = [self._compute_otsu_threshold(img[0] if img.ndim == 3 else img) for img in images]
        self.fitted_threshold = float(np.mean(thresholds))
        self.is_fitted = True
        return self

    def predict(self, chip: np.ndarray) -> np.ndarray:
        """Predict binary flood mask (1 for water, 0 for dry).

        Water has backscatter lower than threshold.
        """
        # chip: (H, W) or (1, H, W) or (B, 1, H, W)
        thresh = self.fitted_threshold if self.is_fitted else self._compute_otsu_threshold(chip)
        return (chip < thresh).astype(np.uint8)


class BackscatterDifferencingBaseline:
    """Normalized multi-temporal backscatter differencing baseline.

    Computes normalized difference ratio: D = (pre - post) / (pre + post + eps).
    Positive difference indicates backscatter drop (inundation).
    """

    def __init__(self, diff_threshold: float = 0.25, eps: float = 1e-4) -> None:
        self.diff_threshold = diff_threshold
        self.eps = eps
        self.is_fitted = True

    def fit(self, pre_chips: np.ndarray, post_chips: np.ndarray, gt_masks: np.ndarray) -> "BackscatterDifferencingBaseline":
        """Fit optimal difference threshold via grid search on training pairs."""
        best_iou = -1.0
        best_t = self.diff_threshold

        for candidate_t in np.linspace(0.10, 0.45, 15):
            ious = []
            for i in range(len(pre_chips)):
                pre = pre_chips[i].squeeze()
                post = post_chips[i].squeeze()
                gt = gt_masks[i].squeeze()

                diff = (pre - post) / (pre + post + self.eps)
                pred = (diff > candidate_t).astype(np.uint8)

                intersection = np.sum((pred == 1) & (gt == 1))
                union = np.sum((pred == 1) | (gt == 1))
                iou = float(intersection / max(1, union))
                ious.append(iou)

            mean_iou = float(np.mean(ious))
            if mean_iou > best_iou:
                best_iou = mean_iou
                best_t = float(candidate_t)

        self.diff_threshold = best_t
        return self

    def predict(self, pre_chip: np.ndarray, post_chip: np.ndarray) -> np.ndarray:
        pre = pre_chip.squeeze()
        post = post_chip.squeeze()
        diff = (pre - post) / (pre + post + self.eps)
        return (diff > self.diff_threshold).astype(np.uint8)


def compute_segmentation_metrics(pred_mask: np.ndarray, gt_mask: np.ndarray) -> dict[str, float]:
    """Compute standard semantic segmentation metrics (IoU, Dice/F1, Precision, Recall)."""
    p = (pred_mask.ravel() > 0.5).astype(int)
    g = (gt_mask.ravel() > 0.5).astype(int)

    tp = int(np.sum((p == 1) & (g == 1)))
    fp = int(np.sum((p == 1) & (g == 0)))
    fn = int(np.sum((p == 0) & (g == 1)))
    tn = int(np.sum((p == 0) & (g == 0)))

    iou = float(tp / max(1, tp + fp + fn))
    dice = float((2 * tp) / max(1, 2 * tp + fp + fn))
    precision = float(tp / max(1, tp + fp))
    recall = float(tp / max(1, tp + fn))
    accuracy = float((tp + tn) / max(1, len(p)))

    return {
        "iou": round(iou, 4),
        "dice_f1": round(dice, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "accuracy": round(accuracy, 4),
    }


__all__ = [
    "BackscatterDifferencingBaseline",
    "OtsuThresholdBaseline",
    "compute_segmentation_metrics",
]
