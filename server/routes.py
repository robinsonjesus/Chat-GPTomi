from flask import request, jsonify
from server.utils import load_session, save_to_session, save_message
from server.config import sessions_collection
from datetime import datetime
import openai

def init_routes(app):
    @app.route('/sessions', methods=['GET'])
    def get_sessions():
        # Get all distinct session IDs
        session_ids = sessions_collection.find().distinct('session_id')
        return jsonify(session_ids)

    @app.route("/session/<session_id>", methods=["GET"])
    def get_chat_history(session_id):
        # Fetch the session document directly
        session_doc = sessions_collection.find_one({"session_id": session_id})
        if not session_doc or "messages" not in session_doc:
            return jsonify({"error": "Session not found"}), 404
        messages = session_doc["messages"]
        # Convert datetime objects to ISO strings for JSON serialization
        for msg in messages:
            if 'timestamp' in msg and isinstance(msg['timestamp'], datetime):
                msg['timestamp'] = msg['timestamp'].isoformat()
        return jsonify(messages)

    @app.route('/session/new', methods=['POST'])
    def create_session():
        data = request.json
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400
        # Initialize a session with a welcome message or empty list
        save_to_session(session_id, role="system", content="")  # optional initial message
        return jsonify({"status": "success"}), 201

    @app.route('/chat', methods=['POST'])
    def chat():
        data = request.get_json()
        session_id = data.get("session_id")
        user_prompt = data.get("prompt")

        if not session_id or not user_prompt:
            return jsonify({"error": "Missing session_id or prompt"}), 400

        # Save user's message
        save_message(session_id, role="user", content=user_prompt)

        # Load full chat history for context
        messages = load_session(session_id)

        # Generate response via OpenAI API
        try:
            response = openai.chat.completions.create(
                model="gpt-4.1-nano",
                messages=messages
            )
            print(response)
            assistant_response = response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            assistant_response = "Sorry, I couldn't process that."

        # Save assistant's reply
        save_message(session_id, role="assistant", content=assistant_response)

        return jsonify({"response": assistant_response})
    
    @app.route('/rename-session', methods=['POST'])
    def rename_session():
        data = request.get_json()
        old_id = data.get('old_id')
        new_id = data.get('new_id')
        if not old_id or not new_id:
            return jsonify({"error": "Missing old_id or new_id"}), 400
        
        # Update all documents with old_id to new_id
        result = sessions_collection.update_many(
            {"session_id": old_id},
            {"$set": {"session_id": new_id}}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "Old session not found"}), 404
        
        return jsonify({"status": "success"})
    
    @app.route('/session/<session_id>', methods=['DELETE'])
    def delete_session(session_id):
        result = sessions_collection.delete_one({"session_id": session_id})
        if result.deleted_count == 0:
            return jsonify({"error": "Session not found"}), 404
        return jsonify({"status": "deleted"})    