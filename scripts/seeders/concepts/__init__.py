"""Сидеры для концептов (UI и Domain)"""

from scripts.seeders.concepts.domain_concepts_seeder import DomainConceptsSeeder
from scripts.seeders.concepts.ui_concepts_seeder import UIConceptsSeeder

__all__ = ["UIConceptsSeeder", "DomainConceptsSeeder"]
