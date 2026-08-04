"""Health check endpoint router."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])

# Will be injected from main.py
session_service = None


def init_dependencies(session_svc):
    """Initialize router dependencies."""
    global session_service
    session_service = session_svc


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/debug/sessions")
async def list_sessions():
    """
    List all active sessions with chat_ids.
    
    Useful for finding chat_ids of users who have messaged the bot.
    """
    if not session_service:
        return {"error": "Session service not initialized"}
    
    # Access the internal sessions dict
    sessions = session_service._sessions
    
    result = {
        "total_sessions": len(sessions),
        "chat_ids": list(sessions.keys()),
        "sessions": [
            {
                "chat_id": chat_id,
                "created_at": session.get("created_at").isoformat() if session.get("created_at") else None,
                "message_count": len(session.get("conversation_history", [])),
                "record_complete": session.get("intake_record", {}).is_complete() if hasattr(session.get("intake_record", {}), "is_complete") else False
            }
            for chat_id, session in sessions.items()
        ]
    }
    
    return result
