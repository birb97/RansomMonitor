# collectors/__init__.py
"""
Collector modules for retrieving data from ransomware intelligence sources.

This package provides collectors for different intelligence sources:
- BaseCollector: Abstract base class for all collectors
- RansomlookCollector: Collector for Ransomlook API
- RansomwareLiveCollector: Collector for Ransomware.live API
- DropletProxyCollector: Base collector for .onion sites via Droplet proxy
- OnionCollector: Base collector for ransomware onion sites with fallback support
- OmegalockCollector: Collector for Omega Lock ransomware group
- RansomwatchCollector: Collector for Ransomwatch API
"""

# Import collector classes to make them available at package level
from .base import BaseCollector
from .ransomlook import RansomlookCollector
from .ransomwarelive import RansomwareLiveCollector
from .droplet_proxy import DropletProxyCollector
from .onion_base import OnionCollector
from .omegalock import OmegalockCollector
from .ransomwatch import RansomwatchCollector

# Define what's available when using "from collectors import *"
__all__ = [
    'BaseCollector', 
    'RansomlookCollector', 
    'RansomwareLiveCollector',
    'DropletProxyCollector',
    'OnionCollector',
    'OmegalockCollector',
    'RansomwatchCollector'
]