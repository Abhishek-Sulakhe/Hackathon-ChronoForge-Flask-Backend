# roast_app/routes/interactive_routes.py
import uuid
from flask import Blueprint, request, jsonify
from aura_flow.db_utils import conversations, format_chat_history
from aura_flow.ai_core import (
    roast_opponent_chain,
    realtime_comedy_feedback_chain,
    final_performance_review_chain
)

# Create a Blueprint for these routes
roast_trainer_bp = Blueprint('roast_trainer', __name__)

@roast_trainer_bp.route('/start_roast', methods=['POST'])
def start_roast():
    """Starts a new interactive roast battle session."""
    data = request.get_json()
    # Topic is now optional for a roast
    topic = data.get('topic') 
    session_id = str(uuid.uuid4())

    conversations.insert_one({
        "_id": session_id,
        "topic": topic, # Can be None
        "messages": [],
        "status": "active"
    })

    if topic:
        opening_statement = f"Alright, let's do this. The theme for this roast is: '{topic}'. You're up first. Try to make it funny."
    else:
        opening_statement = "So you think you're funny? The roast battle starts now. You go first. Don't hold back."

    return jsonify({
        "message": "Roast battle started successfully.",
        "session_id": session_id,
        "opening_statement": opening_statement
    }), 201

@roast_trainer_bp.route('/roast_turn', methods=['POST'])
def roast_turn():
    """Handles a turn-by-turn message in an ongoing roast battle."""
    data = request.get_json()
    session_id = data.get('session_id')
    user_message = data.get('message')

    if not session_id or not user_message:
        return jsonify({"error": "session_id and message are required"}), 400

    convo = conversations.find_one({"_id": session_id})
    if not convo or convo.get("status") != "active":
        return jsonify({"error": "Invalid or completed session ID"}), 404

    chat_history_formatted = format_chat_history(convo['messages'])
    
    # Get the AI's comeback and real-time feedback on the user's roast
    comedy_feedback = realtime_comedy_feedback_chain.invoke({"user_input": user_message})
    roast_comeback = roast_opponent_chain.invoke({
        "chat_history": chat_history_formatted,
        "user_input": user_message
        # No topic is needed for the opponent's comeback
    })

    # Update database with the new turn
    new_messages = [
        {"role": "user", "content": user_message},
        {"role": "ai", "content": roast_comeback}
    ]
    conversations.update_one(
        {"_id": session_id},
        {"$push": {"messages": {"$each": new_messages}}}
    )

    return jsonify({
        "roast_comeback": roast_comeback,
        "comedy_feedback": comedy_feedback
    })

@roast_trainer_bp.route('/end_roast', methods=['POST'])
def end_roast():
    """Ends a roast battle and provides a final review of the user's performance."""
    data = request.get_json()
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    convo = conversations.find_one({"_id": session_id})
    if not convo:
        return jsonify({"error": "Invalid session ID"}), 404

    full_history = format_chat_history(convo['messages'])
    if not convo['messages']:
        return jsonify({"final_review": "You didn't say anything! No roasts, no review."})

    # Generate the final performance review
    final_review = final_performance_review_chain.invoke({"chat_history": full_history})
    
    conversations.update_one(
        {"_id": session_id},
        {"$set": {"status": "completed"}}
    )
    return jsonify({"final_review": final_review})