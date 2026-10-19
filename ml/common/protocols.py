"""Protocol definition for ASTRA-GUARD Risk Modules."""
from typing import Any, Protocol, runtime_checkable

from ml.common.schemas import Attribution, ModuleResult


@runtime_checkable
class RiskModule(Protocol):
    """Common interface contract for all AI domains (health, debris, disaster)."""
    name: str
    version: str

    def fit(self, data: Any) -> None:
        """Fit or calibrate the module on training/nominal data."""
        ...

    def score(self, window: Any) -> ModuleResult:
        """Evaluate a window of data and return normalized risk score and evidence."""
        ...

    def explain(self, window: Any, result: ModuleResult) -> list[Attribution]:
        """Produce attributions/drivers for the evaluated window."""
        ...
