from werkzeug.security import generate_password_hash
from server.config import users_collection

def add_user_to_db(username, password, role):
    hashed_pw = generate_password_hash(password)
    users_collection.insert_one({
        "username": username,
        "password": hashed_pw,
        "role": role
    })
