"""
Модульная система инициализации базы данных
Построена на принципах SOLID для легкого расширения и поддержки
"""

from scripts.seeders.base import BaseSeeder, SeederRegistry
from scripts.seeders.orchestrator import SeederOrchestrator

__all__ = ["BaseSeeder", "SeederRegistry", "SeederOrchestrator"]
