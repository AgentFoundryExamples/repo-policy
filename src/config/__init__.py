"""Configuration loading and schema for repo-policy."""

from .loader import load_config
from .schema import Config

__all__ = ["load_config", "Config"]
