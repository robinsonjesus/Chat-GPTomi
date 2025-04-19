from flask import Flask, send_from_directory
from server.routes import init_routes
from server.config import openai

def create_app():
    app = Flask(__name__, static_folder='static')
    
    # Route to serve index.html at root
    @app.route('/')
    def index():
        return send_from_directory('static', 'index.html')
    
    # Route to serve static files (css, js)
    @app.route('/static/<path:path>')
    def static_files(path):
        return send_from_directory('static', path)
    
    # Initialize your API routes
    init_routes(app)
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)