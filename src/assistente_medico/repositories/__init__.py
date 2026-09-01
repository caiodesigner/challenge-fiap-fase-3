"""Persistência estruturada de prontuários sintéticos."""

from .clinical import ClinicalRepository, PatientNotFoundError
from .seed import build_database

__all__ = ["ClinicalRepository", "PatientNotFoundError", "build_database"]
