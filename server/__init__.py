from flask import Flask, send_from_directory
from server.routes import init_routes
from dotenv import load_dotenv
import os

def create_app():
    load_dotenv()
    app = Flask(__name__, static_folder='static')  # specify static folder
    
    # Route to serve index.html at root
    @app.route('/')
    def index():
        return send_from_directory('static', 'index.html')
    
    # Route to serve static files (css, js)
    @app.route('/static/<path:path>')
    def static_files(path):
        return send_from_directory('static', path)
    
    # Initialize API routes
    init_routes(app)
    return app