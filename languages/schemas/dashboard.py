from dataclasses import dataclass
from typing import Optional

import strawberry
from sqlalchemy import func
from strawberry.types import Info

from languages.models.concept import ConceptModel
from languages.models.dictionary import DictionaryModel
from languages.models.language import LanguageModel


@strawberry.type(description="Aggregated counters for dashboard widgets.")
class DashboardCounts:
    concepts: int = strawberry.field(description="Total number of concepts.")
    languages: int = strawberry.field(description="Total number of languages.")
    dictionaries: int = strawberry.field(description="Total number of dictionaries.")


@strawberry.type
class DashboardQuery:
    """Public Dashboard helper queries."""

    @strawberry.field(name="dashboardStats", description="Get aggregated counts used by the dashboard widgets.")
    def dashboard_stats(self, info: Info) -> DashboardCounts:
        db = info.context["db"]

        concepts_count = db.query(func.count(ConceptModel.id)).scalar() or 0
        languages_count = db.query(func.count(LanguageModel.id)).scalar() or 0
        dictionaries_count = db.query(func.count(DictionaryModel.id)).scalar() or 0

        return DashboardCounts(
            concepts=concepts_count,
            languages=languages_count,
            dictionaries=dictionaries_count,
        )
