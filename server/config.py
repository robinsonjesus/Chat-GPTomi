import os
import openai
from pymongo import MongoClient

# Set your OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# MongoDB setup
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["chat_db"]
sessions_collection = db["sessions"]
users_collection = db["users"]