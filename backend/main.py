"""Entrypoint forwarding to app.main for backward compatibility and CLI convenience."""
import os
import sys

# Ensure current directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import app

__all__ = ["app"]
