from backend.app.api.document_routes import router as document_router
from backend.app.api.user_routes import router as user_router
from backend.app.api.chat_routes import router as chat_router

__all__ = ["user_router", "document_router", "chat_router"]
