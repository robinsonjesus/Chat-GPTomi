from server.config import sessions_collection
import html
from datetime import datetime

def load_session(session_id):
    session = sessions_collection.find_one({"session_id": session_id})
    return session["messages"] if session else []

def save_to_session(session_id, role, content):
    # Sanitize user content
    sanitized_content = html.escape(content) if role == "user" else content
    session = sessions_collection.find_one({"session_id": session_id})
    messages = session.get("messages", []) if session else []
    messages.append({"role": role, "content": sanitized_content})
    sessions_collection.update_one(
        {"session_id": session_id},
        {"$set": {"session_id": session_id, "messages": messages}},
        upsert=True
    )

# New function to append a message to existing session
def save_message(session_id, role, content):
    sessions_collection.update_one(
        {"session_id": session_id},
        {"$push": {"messages": {"role": role, "content": content, "timestamp": datetime.utcnow()}}},
        upsert=True
    )