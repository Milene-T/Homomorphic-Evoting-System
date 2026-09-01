from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import pickle

app = Flask(__name__)
CORS(app)

grand_ciphertext = 1
ballot_counter = 0
public_key_n = None

def load_election_parameters():
    global public_key_n
    try:
        with open("election_secrets.dat", "rb") as f:
            data = pickle.load(f)
            public_key_n = int(data["pub"][0])
        print(f"[BALLOT BOX INIT] Synchronized public parameter 'n' successfully.")
    except Exception:
        print("[BALLOT BOX ERROR] Core election parameters file missing! Start Server 5002 first.")

@app.route('/cast_ballot', methods=['POST'])
def cast_ballot():
    global grand_ciphertext, ballot_counter, public_key_n
    
    if not public_key_n:
        load_election_parameters()

    data = request.get_json()
    token = data.get("token")
    encrypted_vote = int(data.get("ciphertext"))
    
    print(f"\n[BALLOT BOX NETWORK] Incoming processing event...")
    print(f" -> Token presented: {token[:12]}...")
    print(f" -> Encrypted payload block: {str(encrypted_vote)[:40]}...")

    # Cross-verify token validity with Registration Server
    try:
        res = requests.post("http://127.0.0.1:5002/verify_token", json={"token": token})
        if not res.json().get("valid"):
            print(" [-] Validation rejection: Token is expired or invalid.")
            return jsonify({"status": "ERROR", "message": "Invalid/Spent token authorization."}), 403
    except Exception:
        return jsonify({"status": "ERROR", "message": "Identity network link failed."}), 500
        
    # HOMOMORPHIC LOGIC: C_total = (C_old * C_new) mod n^2
    n_sq = public_key_n * public_key_n
    grand_ciphertext = (grand_ciphertext * encrypted_vote) % n_sq
    ballot_counter += 1
    
    print(f" [+] Success: Vault aggregate multiplied. Registered ballots: {ballot_counter}")
    return jsonify({"status": "SUCCESS", "message": "Encrypted ballot accepted and homomorphically compiled."})

@app.route('/get_tally', methods=['GET'])
def get_tally():
    return jsonify({
        "grand_ciphertext": str(grand_ciphertext),
        "total_ballots": ballot_counter
    })

if __name__ == '__main__':
    print("="*60)
    print("STARTING HOMOMORPHIC BALLOT BOX SERVER ON PORT 5003...")
    print("="*60)
    load_election_parameters()
    app.run(port=5003, debug=False)