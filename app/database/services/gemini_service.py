from .ollama_service import OllamaService


class GeminiService(OllamaService):
    """Backward-compatible alias. The project now uses Ollama instead of Gemini."""
