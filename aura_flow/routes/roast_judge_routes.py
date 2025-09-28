import json
from flask import Blueprint, request, jsonify
from aura_flow.ai_core import (
    roast_judge_chain,  # Changed from winner_judge_chain
    coach_chain         # Assuming this is the roast-specific coach chain
)

# Create a Blueprint for these routes
roast_battle_bp = Blueprint('roast_battle', __name__)


@roast_battle_bp.route('/analyze_roast', methods=['POST'])
def analyze_roast():
    """Analyzes a complete roast battle transcript provided in a single JSON payload."""
    data = request.get_json()
    if not data or 'roast' not in data or not isinstance(data['roast'], list):
        return jsonify({"error": "Request must be JSON with a 'roast' key containing a list of turns."}), 400

    roast_turns = data.get('roast', [])

    # Part 1: Judge the winner
    # Create a clean transcript from the list of turns
    transcript = "\n".join([f"{turn.get('player', 'Unknown')}: {turn.get('speech', '')}" for turn in roast_turns])
    
    try:
        # The roast judge chain doesn't need a topic
        judgement_json = roast_judge_chain.invoke({"transcript": transcript})
        # The JsonOutputParser should return a dict directly, so json.loads may not be needed
        judgement = judgement_json if isinstance(judgement_json, dict) else json.loads(judgement_json)
    except (json.JSONDecodeError, TypeError) as e:
        return jsonify({
            "error": "Failed to parse the judgment from the AI.",
            "raw_output": str(judgement_json) # Use the raw output before parsing attempt
        }), 500

    # Part 2: Provide individual coaching on roast performance
    player_texts = {}
    for turn in roast_turns:
        player, speech = turn.get('player'), turn.get('speech')
        if player and speech:
            player_texts.setdefault(player, []).append(speech)

    roast_analyses = {}
    for player, speeches in player_texts.items():
        full_text = "\n".join(speeches)
        roast_analyses[player] = coach_chain.invoke({"player_text": full_text})
        
    # Part 3: Combine and return
    return jsonify({
        "judgement": judgement,
        "roast_analysis": roast_analyses
    })