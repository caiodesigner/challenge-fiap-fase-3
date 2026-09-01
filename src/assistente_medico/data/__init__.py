"""Preparação, geração e validação dos dados do projeto."""

from .synthetic import generate_dataset
from .validation import DatasetValidationError, validate_dataset

__all__ = ["DatasetValidationError", "generate_dataset", "validate_dataset"]
