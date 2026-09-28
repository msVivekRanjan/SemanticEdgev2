"""
nvr/assistant/__init__.py
------------------------
Internal SemanticEdge Assistant Service package.
"""

from .service import AssistantService
from .tools import NVRTools

__all__ = ["AssistantService", "NVRTools"]
