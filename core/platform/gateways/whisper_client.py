import io
import urllib.request
import urllib.error
import json
import os
import uuid

from core.platform.logging.structured_logging import get_logger

logger = get_logger(__name__)


class WhisperClient:
    """HTTP-клиент для whisper-service gateway."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("WHISPER_GATEWAY_URL", "http://gateway-whisper:8010")).rstrip("/")

    def transcribe(self, audio_bytes: bytes, filename: str = "audio.webm", language: str = "ru") -> str:
        """Отправляет аудио в whisper-service, возвращает распознанный текст."""
        boundary = uuid.uuid4().hex
        body = _build_multipart(boundary, filename, audio_bytes)
        content_type = f"multipart/form-data; boundary={boundary}"

        req = urllib.request.Request(
            f"{self.base_url}/transcribe",
            data=body,
            headers={"Content-Type": content_type},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return data.get("text", "")
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode(errors="replace")
            logger.error("whisper gateway error %s: %s", exc.code, body_text)
            raise RuntimeError(f"Whisper gateway returned {exc.code}: {body_text}") from exc
        except Exception as exc:
            logger.error("whisper gateway unreachable: %s", exc)
            raise RuntimeError(f"Whisper gateway unreachable: {exc}") from exc

    def health(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.base_url}/health", timeout=5):
                return True
        except Exception:
            return False


def _build_multipart(boundary: str, filename: str, data: bytes) -> bytes:
    buf = io.BytesIO()
    buf.write(f"--{boundary}\r\n".encode())
    buf.write(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    buf.write(b"Content-Type: application/octet-stream\r\n\r\n")
    buf.write(data)
    buf.write(f"\r\n--{boundary}--\r\n".encode())
    return buf.getvalue()
