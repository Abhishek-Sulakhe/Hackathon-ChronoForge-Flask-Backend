# debate_app/routes.py
import uuid
import json
from flask import request, jsonify
from aura_flow import app
from aura_flow.db_utils import conversations, format_chat_history
from aura_flow.ai_core import (
    debate_chain,
    language_feedback_chain,
    final_judgement_chain,
    winner_judge_chain,
    coach_chain
)

# --- INTERACTIVE DEBATE ENDPOINTS ---

@app.route('/start_debate', methods=['POST'])
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

@app.route('/chat', methods=['POST'])
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

@app.route('/end_debate', methods=['POST'])
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


# --- ONE-SHOT ANALYSIS ENDPOINT ---

@app.route('/analyze_debate', methods=['POST'])
def analyze_debate():
    """Analyzes a complete debate transcript provided in a single JSON payload."""
    data = request.get_json()
    if not data or 'debate' not in data or not isinstance(data['debate'], list):
        return jsonify({"error": "Request must be JSON with a 'debate' key containing a list of turns."}), 400

    debate_turns = data.get('debate', [])
    topic = data.get('topic', 'An unspecified topic')

    # Part 1: Judge the winner
    transcript = "\n".join([f"{turn.get('player', 'Unknown')}: {turn.get('speech', '')}" for turn in debate_turns])
    
    try:
        judgement_str = winner_judge_chain.invoke({"transcript": transcript, "topic": topic})
        judgement = json.loads(judgement_str)
    except (json.JSONDecodeError, TypeError) as e:
        return jsonify({
            "error": "Failed to parse the judgment from the AI.",
            "raw_output": judgement_str
        }), 500

    # Part 2: Provide individual coaching
    player_texts = {}
    for turn in debate_turns:
        player, speech = turn.get('player'), turn.get('speech')
        if player and speech:
            player_texts.setdefault(player, []).append(speech)

    analyses = {}
    for player, speeches in player_texts.items():
        full_text = "\n".join(speeches)
        analyses[player] = coach_chain.invoke({"player_text": full_text})
        
    # Part 3: Combine and return
    return jsonify({
        "judgement": judgement,
        "language_analysis": analyses
    })