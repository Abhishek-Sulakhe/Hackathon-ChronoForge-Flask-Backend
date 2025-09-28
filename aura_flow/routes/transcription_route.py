
from flask import Blueprint, request, jsonify
from deepgram import  PrerecordedOptions
from aura_flow.ai_core import deepgram

transcription_bp = Blueprint('transcription', __name__)

@transcription_bp.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    audio_file = request.files["audio"]

    # Prepare audio source
    source = {
        "buffer": audio_file.read(),
        "mimetype": "audio/webm"   # or audio/wav if frontend sends wav
    }

    options = PrerecordedOptions(
        model="nova-3",
        smart_format=True,
    )

    # Use new API path
    response = deepgram.listen.prerecorded.v("1").transcribe_file(source, options)

    transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]

    return jsonify({"message": transcript})