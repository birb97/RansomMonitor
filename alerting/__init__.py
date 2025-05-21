# alerting/__init__.py
"""
Alert generation, processing, and notification modules.

This package provides:
- Alert trigger mechanisms for matching claims
- Notification methods for delivering alerts
"""

# Import alerting classes to make them available at package level
from .triggers import AlertTrigger
from .notifiers import ConsoleNotifier, EmailNotifier, WebhookNotifier

# Define what's available when using "from alerting import *"
__all__ = ['AlertTrigger', 'ConsoleNotifier', 'EmailNotifier', 'WebhookNotifier']