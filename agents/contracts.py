from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
	valid: bool
	errors: list[str] = field(default_factory=list)


@dataclass
class InteractionResult:
	drug1_name: str
	drug2_name: str
	base_severity: str
	escalated_severity: str
	source: str
	description: str = ""
	recommendation: str = ""
	metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CareGapResult:
	condition: str
	screening: str
	overdue_years: float
	guideline: str
	recommendation: str = ""
	metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HistoryDeltaResult:
	delta_summary: str
	narrative_text: str
	language: str = "en"
