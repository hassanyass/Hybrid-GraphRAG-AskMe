from backend.app.api.document_routes import router as document_router
from backend.app.api.user_routes import router as user_router
from backend.app.api.chat_routes import router as chat_router
from backend.app.api.audio_routes import router as audio_router
from backend.app.api.auth_routes import router as auth_router
from backend.app.api.workspace_routes import router as workspace_router
from backend.app.api.conversation_routes import router as conversation_router

__all__ = ["user_router", "document_router", "chat_router", "audio_router", "auth_router", "workspace_router", "conversation_router"]
