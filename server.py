from flask import Flask, request, jsonify, send_from_directory, abort
from dotenv import load_dotenv
import os
import openai
import json
from datetime import datetime
import html
from openai import OpenAI
import pymongo
from pymongo import MongoClient

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key
client = OpenAI(api_key=api_key)


# Initialize Flask app
app = Flask(__name__)

# MongoDB setup
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["chat_db"]  # Database name
sessions_collection = db["sessions"]  # Collection to store sessions

# --- Utility: Save a message to a session in MongoDB ---
def save_to_session(session_id, role, content):
    # Escape user input but NOT assistant markdown
    sanitized_content = html.escape(content) if role == "user" else content
    
    # Check if the session already exists in MongoDB
    session = sessions_collection.find_one({"session_id": session_id})
    if session:
        messages = session.get("messages", [])
    else:
        messages = []

    messages.append({"role": role, "content": sanitized_content})

    # Update or insert the session into MongoDB
    sessions_collection.update_one(
        {"session_id": session_id},
        {"$set": {"session_id": session_id, "messages": messages}},
        upsert=True
    )

# --- Utility: Load messages from session in MongoDB ---
def load_session(session_id):
    session = sessions_collection.find_one({"session_id": session_id})
    if session:
        return session["messages"]
    return []

# --- Create a new session in MongoDB ---
@app.route("/session/new", methods=["POST"])
def new_session():
    data = request.get_json()
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    # Insert an empty session in MongoDB
    sessions_collection.insert_one({"session_id": session_id, "messages": []})
    return jsonify({"status": "created", "session_id": session_id}), 200

# --- Handle chat input/output ---
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    prompt = data.get("prompt", "")
    session_id = data.get("session_id", datetime.now().strftime("%Y%m%d_%H%M%S"))
    model = data.get("model", "gpt-4")

    messages = load_session(session_id)
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )

        reply = response.choices[0].message.content.strip()

        # Save user and assistant messages in MongoDB
        save_to_session(session_id, "user", prompt)
        save_to_session(session_id, "assistant", reply)

        return jsonify({"response": reply, "session_id": session_id})

    except Exception as e:
        print("OpenAI API error:", e)
        return jsonify({"error": "API request failed", "details": str(e)}), 500

# --- Return a list of available session IDs ---
@app.route("/sessions", methods=["GET"])
def get_sessions():
    session_ids = [session["session_id"] for session in sessions_collection.find()]
    return jsonify(sorted(session_ids, reverse=True))

# --- Load specific session by ID ---
@app.route("/session/<session_id>", methods=["GET"])
def get_session(session_id):
    messages = load_session(session_id)
    return jsonify(messages)

# --- Delete a session ---
@app.route("/session/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    result = sessions_collection.delete_one({"session_id": session_id})
    if result.deleted_count > 0:
        return jsonify({"success": True})
    return abort(404, "Session not found")

# --- Rename a session ---
@app.route("/rename-session", methods=["POST"])
def rename_session():
    data = request.get_json()
    old_id = data.get("old_id")
    new_id = data.get("new_id")

    old_session = sessions_collection.find_one({"session_id": old_id})
    if not old_session:
        return abort(404, "Original session not found")
    
    new_session = sessions_collection.find_one({"session_id": new_id})
    if new_session:
        return abort(400, "Target session name already exists")

    sessions_collection.update_one(
        {"session_id": old_id},
        {"$set": {"session_id": new_id}}
    )

    return jsonify({"success": True})

# --- Serve static front-end file ---
@app.route("/")
def home():
   return send_from_directory("static", "index.html")

@app.route("/models")
def get_models():
    return send_from_directory("static", "models.json")

if __name__ == "__main__":
    app.run(debug=True)