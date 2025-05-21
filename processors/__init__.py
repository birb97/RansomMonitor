# processors/__init__.py
"""
Data processing modules for handling and transforming ransomware data.

This package provides utilities for:
- Extracting network identifiers from claim data
- Validating data integrity
"""

# Import processor classes to make them available at package level
from .extractors import NetworkIdentifierExtractor
from .validators import DataValidator

# Define what's available when using "from processors import *"
__all__ = ['NetworkIdentifierExtractor', 'DataValidator']