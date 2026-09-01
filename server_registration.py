from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import secrets
import pickle
import os
from crypto_engine import generate_paillier_keys

app = Flask(__name__, template_folder='templates')
CORS(app) # Allows cross-port communication between templates and servers

# Mock Voter Database
VOTER_REGISTRY = {
    "voter1": {"name": "Alice", "has_voted": False},
    "voter2": {"name": "Bob", "has_voted": False},
    "voter3": {"name": "Charlie", "has_voted": False},
    "voter4": {"name": "David", "has_voted": False},
    "voter5": {"name": "Moh", "has_voted": False}
}

ISSUED_TOKENS = set()

# Initialize Global Election Cryptography Keys on startup
pub_key, priv_key = generate_paillier_keys()
with open("election_secrets.dat", "wb") as f:
    pickle.dump({"pub": pub_key, "priv": priv_key}, f)

@app.route('/')
def voter_interface():
    # Renders the HTML voting window interface directly
    return render_template('voter.html')

@app.route('/get_public_key', methods=['GET'])
def get_public_key():
    return jsonify({"n": str(pub_key[0]), "g": str(pub_key[1])})

@app.route('/authenticate', methods=['POST'])
def authenticate_voter():
    data = request.get_json()
    voter_id = data.get("voter_id")
    
    if voter_id not in VOTER_REGISTRY:
        print(f"[REGISTRATION WARNING] Access denied for invalid ID: {voter_id}")
        return jsonify({"status": "REJECTED", "message": "Identity unknown to this registry."}), 401
        
    if VOTER_REGISTRY[voter_id]["has_voted"]:
        print(f"[REGISTRATION WARNING] Blocked double-voting attempt by: {voter_id}")
        return jsonify({"status": "REJECTED", "message": "Identity has already consumed its single window ballot allocation."}), 403
        
    # Lock single window
    VOTER_REGISTRY[voter_id]["has_voted"] = True
    
    token = secrets.token_hex(16)
    ISSUED_TOKENS.add(token)
    
    print(f"[REGISTRATION ACTION] Authenticated {voter_id}. Dispatched anonymous token: {token}")
    return jsonify({"status": "AUTHORIZED", "token": token})

@app.route('/verify_token', methods=['POST'])
def verify_token():
    data = request.get_json()
    token = data.get("token")
    if token in ISSUED_TOKENS:
        ISSUED_TOKENS.remove(token) # Consume instantly
        print(f"[REGISTRATION DB] Anonymous Token validated and permanently consumed.")
        return jsonify({"valid": True})
    return jsonify({"valid": False})

if __name__ == '__main__':
    print("="*60)
    print("STARTING IDENTITY REGISTRATION SERVER ON PORT 5002...")
    print("="*60)
    app.run(port=5002, debug=False)