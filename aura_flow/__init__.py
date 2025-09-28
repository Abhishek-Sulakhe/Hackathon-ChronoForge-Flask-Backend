# debate_app/__init__.py
import os
from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# Connect to MongoDB
try:
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client.debate_chatbot_db  # Use or create a database
    print("✅ Successfully connected to MongoDB.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()


from aura_flow.routes.transcription_route import transcription_bp

from aura_flow.routes.roast_judge_routes import roast_battle_bp
from aura_flow.routes.roast_trainer import roast_trainer_bp


from aura_flow.routes.debate_judge_routes import debate_judge_bp
from aura_flow.routes.debate_trainer import debate_trainer_bp

# Register the Blueprints with the Flask app
# All routes defined in those files will now be active.
app.register_blueprint(transcription_bp)

app.register_blueprint(debate_trainer_bp)
app.register_blueprint(debate_judge_bp)

app.register_blueprint(roast_trainer_bp)
app.register_blueprint(roast_battle_bp)