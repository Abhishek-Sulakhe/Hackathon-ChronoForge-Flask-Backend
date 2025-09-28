# debate_app/db_utils.py
from aura_flow import db

# Define the collection from the initialized db object
conversations = db.conversations

def format_chat_history(messages):
    """Formats the chat history from the database into a readable string."""
    if not messages:
        return "No history yet."
    history = ""
    for msg in messages:
        role = "User" if msg["role"] == "user" else "Opponent"
        history += f'{role}: {msg["content"]}\n'
    return history.strip()