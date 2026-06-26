from __future__ import annotations

from typing import Optional

import strawberry

from core.models.rag import RagDocument, RagProject


# ─── Types ───────────────────────────────────────────────────────────────────

@strawberry.type
class RagProjectType:
    id: int
    name: str
    description: Optional[str]
    embedding_model: str
    embedding_dim: int
    chunk_size: int
    chunk_overlap: int
    is_active: bool


@strawberry.type
class RagDocumentType:
    id: int
    project_id: int
    source_type: str
    source_uri: str
    title: Optional[str]
    status: str
    error_message: Optional[str]
    chunk_count: int
    indexed_at: Optional[str]


@strawberry.type
class RagSearchResult:
    chunk_id: int
    content: str
    score: float
    document_id: int
    document_title: Optional[str]
    chunk_index: int


# ─── Inputs ──────────────────────────────────────────────────────────────────

@strawberry.input
class CreateRagProjectInput:
    name: str
    description: Optional[str] = None
    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768
    chunk_size: int = 512
    chunk_overlap: int = 64


@strawberry.input
class UpdateRagProjectInput:
    name: Optional[str] = None
    description: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    is_active: Optional[bool] = None


@strawberry.input
class AddRagDocumentInput:
    project_id: int
    source_type: str
    source_uri: str
    title: Optional[str] = None


# ─── Queries ─────────────────────────────────────────────────────────────────

@strawberry.type
class RagQuery:
    @strawberry.field(description="Список RAG-проектов.")
    def rag_projects(
        self, info: strawberry.Info, active_only: bool = False
    ) -> list[RagProjectType]:
        from core.domains.rag import RagService
        return [
            _project(p)
            for p in RagService(info.context["db"]).get_projects(active_only=active_only)
        ]

    @strawberry.field(description="RAG-проект по ID.")
    def rag_project(
        self, info: strawberry.Info, project_id: int
    ) -> Optional[RagProjectType]:
        from core.domains.rag import RagService
        p = RagService(info.context["db"]).get_project(project_id)
        return _project(p) if p else None

    @strawberry.field(description="Документы проекта. Опционально фильтр по статусу.")
    def rag_documents(
        self,
        info: strawberry.Info,
        project_id: int,
        status: Optional[str] = None,
    ) -> list[RagDocumentType]:
        from core.domains.rag import RagService
        return [
            _document(d)
            for d in RagService(info.context["db"]).get_documents(project_id, status=status)
        ]

    @strawberry.field(
        description="Семантический поиск по проекту. Возвращает top_k чанков, "
                    "отсортированных по косинусной близости."
    )
    def rag_search(
        self,
        info: strawberry.Info,
        project_id: int,
        query: str,
        top_k: int = 5,
    ) -> list[RagSearchResult]:
        from core.domains.rag import RagService
        results = RagService(info.context["db"]).search(project_id, query, top_k)
        return [
            RagSearchResult(
                chunk_id=r["chunk_id"],
                content=r["content"],
                score=r["score"],
                document_id=r["document_id"],
                document_title=r.get("document_title"),
                chunk_index=r["chunk_index"],
            )
            for r in results
        ]


# ─── Mutations ───────────────────────────────────────────────────────────────

@strawberry.type
class RagMutation:
    @strawberry.mutation(description="Создать новый RAG-проект.")
    def create_rag_project(
        self, info: strawberry.Info, input: CreateRagProjectInput
    ) -> RagProjectType:
        from core.domains.rag import RagService
        p = RagService(info.context["db"]).create_project(
            name=input.name,
            description=input.description,
            embedding_model=input.embedding_model,
            embedding_dim=input.embedding_dim,
            chunk_size=input.chunk_size,
            chunk_overlap=input.chunk_overlap,
        )
        return _project(p)

    @strawberry.mutation(description="Обновить настройки RAG-проекта.")
    def update_rag_project(
        self, info: strawberry.Info, project_id: int, input: UpdateRagProjectInput
    ) -> RagProjectType:
        from core.domains.rag import RagService
        p = RagService(info.context["db"]).update_project(
            project_id,
            name=input.name,
            description=input.description,
            chunk_size=input.chunk_size,
            chunk_overlap=input.chunk_overlap,
            is_active=input.is_active,
        )
        return _project(p)

    @strawberry.mutation(description="Удалить RAG-проект вместе с документами и чанками.")
    def delete_rag_project(self, info: strawberry.Info, project_id: int) -> bool:
        from core.domains.rag import RagService
        return RagService(info.context["db"]).delete_project(project_id)

    @strawberry.mutation(description="Добавить документ в проект (статус pending).")
    def add_rag_document(
        self, info: strawberry.Info, input: AddRagDocumentInput
    ) -> RagDocumentType:
        from core.domains.rag import RagService
        d = RagService(info.context["db"]).add_document(
            project_id=input.project_id,
            source_type=input.source_type,
            source_uri=input.source_uri,
            title=input.title,
        )
        return _document(d)

    @strawberry.mutation(
        description="Запустить индексацию документа: загрузить источник, "
                    "разбить на чанки, получить эмбеддинги через Ollama."
    )
    def index_rag_document(self, info: strawberry.Info, document_id: int) -> RagDocumentType:
        from core.domains.rag import RagService
        d = RagService(info.context["db"]).index_document(document_id)
        return _document(d)

    @strawberry.mutation(description="Удалить документ и все его чанки.")
    def delete_rag_document(self, info: strawberry.Info, document_id: int) -> bool:
        from core.domains.rag import RagService
        return RagService(info.context["db"]).delete_document(document_id)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _project(p: RagProject) -> RagProjectType:
    return RagProjectType(
        id=p.id,
        name=p.name,
        description=p.description,
        embedding_model=p.embedding_model,
        embedding_dim=p.embedding_dim,
        chunk_size=p.chunk_size,
        chunk_overlap=p.chunk_overlap,
        is_active=p.is_active,
    )


def _document(d: RagDocument) -> RagDocumentType:
    return RagDocumentType(
        id=d.id,
        project_id=d.project_id,
        source_type=str(d.source_type),
        source_uri=d.source_uri,
        title=d.title,
        status=str(d.status),
        error_message=d.error_message,
        chunk_count=d.chunk_count,
        indexed_at=d.indexed_at.isoformat() if d.indexed_at else None,
    )
