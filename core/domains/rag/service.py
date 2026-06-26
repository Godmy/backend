from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.models.rag import DocumentStatus, RagChunk, RagDocument, RagProject, SourceType


class RagService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")

    # ─── Projects ────────────────────────────────────────────────────────

    def get_projects(self, active_only: bool = False) -> list[RagProject]:
        q = self.db.query(RagProject)
        if active_only:
            q = q.filter(RagProject.is_active.is_(True))
        return q.order_by(RagProject.created_at.desc()).all()

    def get_project(self, project_id: int) -> RagProject | None:
        return self.db.query(RagProject).filter(RagProject.id == project_id).first()

    def create_project(
        self,
        name: str,
        description: str | None = None,
        embedding_model: str = "nomic-embed-text",
        embedding_dim: int = 768,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> RagProject:
        project = RagProject(
            name=name,
            description=description,
            embedding_model=embedding_model,
            embedding_dim=embedding_dim,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def update_project(self, project_id: int, **kwargs: Any) -> RagProject:
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        allowed = {"name", "description", "embedding_model", "chunk_size", "chunk_overlap", "is_active"}
        for key, value in kwargs.items():
            if key in allowed and value is not None:
                setattr(project, key, value)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, project_id: int) -> bool:
        project = self.get_project(project_id)
        if not project:
            return False
        self.db.delete(project)
        self.db.commit()
        return True

    # ─── Documents ───────────────────────────────────────────────────────

    def get_documents(self, project_id: int, status: str | None = None) -> list[RagDocument]:
        q = self.db.query(RagDocument).filter(RagDocument.project_id == project_id)
        if status:
            q = q.filter(RagDocument.status == status)
        return q.order_by(RagDocument.created_at.desc()).all()

    def get_document(self, document_id: int) -> RagDocument | None:
        return self.db.query(RagDocument).filter(RagDocument.id == document_id).first()

    def add_document(
        self,
        project_id: int,
        source_type: str,
        source_uri: str,
        title: str | None = None,
    ) -> RagDocument:
        if source_type not in {e.value for e in SourceType}:
            raise ValueError(f"Invalid source_type: {source_type!r}. Use: url, file, text, git")
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        doc = RagDocument(
            project_id=project_id,
            source_type=source_type,
            source_uri=source_uri,
            title=title,
            status=DocumentStatus.pending.value,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def delete_document(self, document_id: int) -> bool:
        doc = self.get_document(document_id)
        if not doc:
            return False
        self.db.delete(doc)
        self.db.commit()
        return True

    # ─── Indexing ────────────────────────────────────────────────────────

    def index_document(self, document_id: int) -> RagDocument:
        doc = self.get_document(document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")
        project = self.get_project(doc.project_id)

        doc.status = DocumentStatus.indexing.value
        doc.error_message = None
        self.db.commit()

        try:
            content = self._fetch_content(doc)
            chunks = self._split_text(content, project.chunk_size, project.chunk_overlap)

            self.db.query(RagChunk).filter(RagChunk.document_id == document_id).delete()

            for idx, chunk_text in enumerate(chunks):
                embedding = self._get_embedding(chunk_text, project.embedding_model)
                self.db.add(RagChunk(
                    document_id=doc.id,
                    project_id=doc.project_id,
                    content=chunk_text,
                    embedding=embedding,
                    chunk_index=idx,
                ))

            doc.status = DocumentStatus.indexed.value
            doc.chunk_count = len(chunks)
            doc.indexed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(doc)
            return doc

        except Exception as exc:
            doc.status = DocumentStatus.error.value
            doc.error_message = str(exc)
            self.db.commit()
            raise

    def _fetch_content(self, doc: RagDocument) -> str:
        if doc.source_type == SourceType.text.value:
            return doc.source_uri
        if doc.source_type == SourceType.url.value:
            with urllib.request.urlopen(doc.source_uri, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        if doc.source_type == SourceType.file.value:
            with open(doc.source_uri, encoding="utf-8", errors="replace") as f:
                return f.read()
        raise ValueError(f"Unsupported source_type: {doc.source_type!r}")

    def _split_text(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            if end == len(text):
                break
            start += chunk_size - overlap
        return chunks

    def _get_embedding(self, text: str, model: str) -> list[float]:
        payload = json.dumps({"model": model, "prompt": text}).encode()
        req = urllib.request.Request(
            f"{self.ollama_host}/api/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return data["embedding"]

    # ─── Search ──────────────────────────────────────────────────────────

    def search(self, project_id: int, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        query_embedding = self._get_embedding(query, project.embedding_model)
        embedding_literal = "[" + ",".join(str(v) for v in query_embedding) + "]"

        rows = self.db.execute(
            text("""
                SELECT
                    c.id            AS chunk_id,
                    c.content,
                    c.chunk_index,
                    c.chunk_metadata,
                    d.id            AS document_id,
                    d.title         AS document_title,
                    1 - (c.embedding <=> CAST(:emb AS vector)) AS score
                FROM rag_chunk c
                JOIN rag_document d ON d.id = c.document_id
                WHERE c.project_id = :project_id
                  AND c.embedding IS NOT NULL
                ORDER BY c.embedding <=> CAST(:emb AS vector)
                LIMIT :top_k
            """),
            {"project_id": project_id, "emb": embedding_literal, "top_k": top_k},
        ).fetchall()

        return [
            {
                "chunk_id": row.chunk_id,
                "content": row.content,
                "chunk_index": row.chunk_index,
                "metadata": row.chunk_metadata,
                "document_id": row.document_id,
                "document_title": row.document_title,
                "score": float(row.score),
            }
            for row in rows
        ]
