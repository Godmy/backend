import os
from pathlib import Path

from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Router


async def serve_upload(request):
    """Отдаёт загруженные пользователями файлы с простой защитой от path traversal."""
    filename = request.path_params["filename"]
    upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads"))
    return _serve_file(upload_dir, filename)


async def serve_export(request):
    """Отдаёт экспортированные файлы (CSV/ZIP и т.д.) с валидацией пути."""
    filename = request.path_params["filename"]
    export_dir = Path(os.getenv("EXPORT_DIR", "exports"))
    return _serve_file(export_dir, filename)


def _serve_file(base_dir: Path, filename: str):
    file_path = (base_dir / filename).resolve()
    if not str(file_path).startswith(str(base_dir.resolve())):
        return JSONResponse({"error": "Invalid file path"}, status_code=400)

    if not file_path.exists():
        return JSONResponse({"error": "File not found"}, status_code=404)

    return FileResponse(file_path)


def register_routes(app: Router) -> None:
    """Регистрирует эндпоинты для статики загрузок/экспорта."""
    app.add_route("/uploads/{filename:path}", serve_upload, methods=["GET"])
    app.add_route("/exports/{filename:path}", serve_export, methods=["GET"])
