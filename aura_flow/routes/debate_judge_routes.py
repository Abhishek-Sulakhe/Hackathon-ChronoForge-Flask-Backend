import json
from flask import Blueprint, request, jsonify
from aura_flow.ai_core import (
    winner_judge_chain,
    coach_chain
)

# Create a Blueprint for these routes
debate_judge_bp = Blueprint('debate_judge', __name__)


@debate_judge_bp.route('/analyze_debate', methods=['POST'])
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