
"""Flask web app for the GHRU voice assistant."""

from __future__ import annotations

import asyncio
import io
import tempfile
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path

from flask import (
    Flask,
    after_this_request,
    jsonify,
    render_template,
    request,
    send_file,
    send_from_directory,
)

from .assistant import AssistantConfig, CollegeVoiceAssistant
from .data import RESPONSES

try:
    import edge_tts
except ImportError:  # pragma: no cover - environment dependent
    edge_tts = None

_TTS_CACHE: OrderedDict[tuple[str, str], bytes] = OrderedDict()
_TTS_CACHE_MAX_ITEMS = 64


def _normalize_language(query: str) -> str:
    lowered = query.strip().lower()
    if "hindi" in lowered or "हिंदी" in lowered or "हिन्दी" in lowered or lowered == "hi":
        return "hi"
    return "en"

@lru_cache(maxsize=2)
def get_assistant(language: str) -> CollegeVoiceAssistant:
    assistant_name = RESPONSES[language]["assistant_name"]
    return CollegeVoiceAssistant(
        AssistantConfig(
            assistant_name=assistant_name,
            language=language,
            use_voice_input=False,
            show_assistant_text=False,
        )
    )


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    project_root = Path(app.root_path).parent
    image_dir = project_root / "image"

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/image/<path:filename>")
    def image_asset(filename: str):
        return send_from_directory(image_dir, filename)

    @app.get("/api/bootstrap")
    def bootstrap():
        intro = "Hello, I am GHRU, your college voice assistant."
        language_prompt = "Choose language. Say or type English or Hindi."
        message = f"{intro} {language_prompt}"
        return jsonify(
            {
                "assistant_name": RESPONSES["en"]["assistant_name"],
                "phase": "language",
                "message": message,
                "speak_message": message,
                "language": "en",
            }
        )

    @app.post("/api/respond")
    def respond():
        payload = request.get_json(silent=True) or {}
        query = str(payload.get("query", "")).strip()
        phase = str(payload.get("phase", "chat")).strip().lower() or "chat"
        current_language = str(payload.get("language", "en")).strip().lower() or "en"

        if phase == "language":
            selected_language = _normalize_language(query)
            speak_text = (
                f"{RESPONSES[selected_language]['language_selected']} "
                f"{RESPONSES[selected_language]['welcome']}"
            )
            response_text = f"{speak_text} {RESPONSES[selected_language]['prompt']}"
            return jsonify(
                {
                    "assistant_name": RESPONSES[selected_language]["assistant_name"],
                    "phase": "chat",
                    "language": selected_language,
                    "message": response_text,
                    "speak_message": response_text,
                    "ended": False,
                }
            )

        assistant = get_assistant(current_language)
        assistant.config.language = current_language
        assistant.config.assistant_name = RESPONSES[current_language]["assistant_name"]

        normalized_query = assistant.normalize_query(query)
        if not normalized_query:
            return jsonify(
                {
                    "assistant_name": assistant.config.assistant_name,
                    "phase": "chat",
                    "language": current_language,
                    "message": RESPONSES[current_language]["prompt"],
                    "speak_message": RESPONSES[current_language]["prompt"],
                    "ended": False,
                }
            )

        if any(word in normalized_query for word in ("exit", "quit", "bye", "close")):
            return jsonify(
                {
                    "assistant_name": assistant.config.assistant_name,
                    "phase": "chat",
                    "language": current_language,
                    "message": RESPONSES[current_language]["goodbye"],
                    "speak_message": RESPONSES[current_language]["goodbye"],
                    "ended": True,
                }
            )

        try:
            response_text = assistant.handle_query(normalized_query)
        except Exception as exc:
            import traceback
            app.logger.error("handle_query error: %s\n%s", exc, traceback.format_exc())
            response_text = (
                "माफ करें, कुछ गड़बड़ हो गई। कृपया दोबारा पूछें।"
                if current_language == "hi"
                else "Sorry, something went wrong on my end. Please try asking again."
            )
        speak_text = response_text
        message = f"{response_text} {RESPONSES[current_language]['prompt']}"
        return jsonify(
            {
                "assistant_name": assistant.config.assistant_name,
                "phase": "chat",
                "language": current_language,
                "message": message,
                "speak_message": message,
                "ended": False,
            }
        )

    @app.post("/api/tts")
    def tts():
        payload = request.get_json(silent=True) or {}
        text = str(payload.get("text", "")).strip()
        language = str(payload.get("language", "en")).strip().lower() or "en"
        if language not in RESPONSES:
            language = "en"

        if not text:
            return jsonify({"error": "Text is required"}), 400
        if edge_tts is None:
            return jsonify({"error": "TTS unavailable"}), 503

        cache_key = (language, text)
        cached_audio = _TTS_CACHE.get(cache_key)
        if cached_audio is not None:
            _TTS_CACHE.move_to_end(cache_key)
            return send_file(io.BytesIO(cached_audio), mimetype="audio/mpeg")

        voice = "hi-IN-SwaraNeural" if language == "hi" else "en-IN-NeerjaNeural"
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            communicator = edge_tts.Communicate(text, voice=voice)
            asyncio.run(communicator.save(str(temp_path)))
            audio_bytes = temp_path.read_bytes()
        except Exception:
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            return jsonify({"error": "Failed to generate audio"}), 503

        _TTS_CACHE[cache_key] = audio_bytes
        _TTS_CACHE.move_to_end(cache_key)
        while len(_TTS_CACHE) > _TTS_CACHE_MAX_ITEMS:
            _TTS_CACHE.popitem(last=False)

        @after_this_request
        def cleanup_file(response):
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            return response

        return send_file(io.BytesIO(audio_bytes), mimetype="audio/mpeg")

    return app


def main() -> int:
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

