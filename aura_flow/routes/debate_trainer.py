
import uuid
import base64
from flask import Blueprint, request, jsonify
from aura_flow.db_utils import conversations, format_chat_history
from aura_flow.ai_core import (
    debate_chain,
    language_feedback_chain,
    final_judgement_chain,
    deepgram,  # Deepgram client is already set up in your ai_core
)
from deepgram import PrerecordedOptions, SpeakOptions

# Create a Blueprint for these routes
debate_trainer_bp = Blueprint('debate_trainer', __name__)

@debate_trainer_bp.route('/start_debate', methods=['POST'])
def start_debate():

    """Starts a new interactive debate session and stores it in the DB."""
    data = request.get_json()
    if not data or 'topic' not in data:
        return jsonify({"error": "Topic is required"}), 400
    


    topic = data['topic']
    session_id = str(uuid.uuid4())

    conversations.insert_one({
        "_id": session_id,
        "topic": topic,
        "messages": [],
        "status": "active"
    })

    opening_statement = f"The debate has begun. The topic is: '{topic}'. I will argue against this. You may present your opening argument."
    return jsonify({
        "message": "Debate started successfully.",
        "session_id": session_id,
        "opening_statement": opening_statement
    }), 201

@debate_trainer_bp.route('/chat', methods=['POST'])
def chat():
    """Handles a turn-by-turn message in an ongoing interactive debate."""
    data = request.get_json()
    session_id = data.get('session_id')
    user_message = data.get('message')

    if not session_id or not user_message:
        return jsonify({"error": "session_id and message are required"}), 400

    convo = conversations.find_one({"_id": session_id})
    if not convo or convo.get("status") != "active":
        return jsonify({"error": "Invalid or completed session ID"}), 404

    chat_history_formatted = format_chat_history(convo['messages'])
    
    # Generate AI responses concurrently for speed (in a real app)
    language_feedback = language_feedback_chain.invoke({"user_input": user_message})
    debate_response = debate_chain.invoke({
        "topic": convo['topic'],
        "chat_history": chat_history_formatted,
        "user_input": user_message
    })

    # Update database with the new turn
    new_messages = [
        {"role": "user", "content": user_message},
        {"role": "ai", "content": debate_response}
    ]
    conversations.update_one(
        {"_id": session_id},
        {"$push": {"messages": {"$each": new_messages}}}
    )

    return jsonify({
        "debate_response": debate_response,
        "language_feedback": language_feedback
    })

@debate_trainer_bp.route('/end_debate', methods=['POST'])
def end_debate():
    """Ends an interactive debate and provides a final judgment on the user's performance."""
    data = request.get_json()
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    convo = conversations.find_one({"_id": session_id})
    if not convo:
        return jsonify({"error": "Invalid session ID"}), 404

    full_history = format_chat_history(convo['messages'])
    if not convo['messages']:
        return jsonify({"final_summary": "No debate took place, so no analysis can be provided."})

    final_summary = final_judgement_chain.invoke({"chat_history": full_history})
    conversations.update_one(
        {"_id": session_id},
        {"$set": {"status": "completed"}}
    )
    return jsonify({"final_summary": final_summary})


