from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import pdfkit

app = Flask(__name__)
CORS(app)

# Load Data
def load_data(file):
    with open(file) as f:
        return json.load(f)

# Save Data
def save_data(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

# Admin Login
@app.route("/admin_login", methods=["POST"])
def admin_login():
    creds = request.form
    users = load_data("users.json")
    if creds['username'] == users['admin']['username'] and creds['password'] == users['admin']['password']:
        return "Admin login successful"
    return "Invalid admin credentials", 401

# Register Candidate
@app.route("/register_candidate", methods=["POST"])
def register_candidate():
    data = request.form
    candidates = load_data("candidates.json")
    candidates['candidates'].append({
        "name": data['name'],
        "flag_url": data['flag_url']
    })
    save_data("candidates.json", candidates)
    return "Candidate registered"

# Register Voter
@app.route("/register_voter", methods=["POST"])
def register_voter():
    data = request.form
    users = load_data("users.json")
    users['voters'].append({
        "voter_id": data['voter_id'],
        "password": data['password'],
        "voted": False
    })
    save_data("users.json", users)
    return "Voter registered"

# Voter Login
@app.route("/voter_login", methods=["POST"])
def voter_login():
    data = request.form
    users = load_data("users.json")
    for voter in users['voters']:
        if voter['voter_id'] == data['voter_id'] and voter['password'] == data['password']:
            if voter['voted']:
                return "Already voted", 403
            return "Login successful"
    return "Invalid credentials", 401

# Vote
@app.route("/vote", methods=["POST"])
def vote():
    data = request.form
    users = load_data("users.json")
    votes = load_data("votes.json")

    # Mark voter as voted
    for voter in users['voters']:
        if voter['voter_id'] == data['voter_id']:
            if voter['voted']:
                return "Already voted", 403
            voter['voted'] = True
            break

    votes['votes'].append({
        "voter_id": data['voter_id'],
        "candidate": data['candidate']
    })

    save_data("users.json", users)
    save_data("votes.json", votes)

    return "Vote cast"

# Get Results
@app.route("/results", methods=["GET"])
def results():
    votes = load_data("votes.json")
    tally = {}
    for vote in votes['votes']:
        name = vote['candidate']
        tally[name] = tally.get(name, 0) + 1
    return jsonify(tally)

# Download as PDF
@app.route("/download_data", methods=["GET"])
def download_data():
    users = load_data("users.json")
    candidates = load_data("candidates.json")
    votes = load_data("votes.json")

    html = f"<h1>Admin Report</h1><h2>Voters</h2>{users}<h2>Candidates</h2>{candidates}<h2>Votes</h2>{votes}"
    pdfkit.from_string(html, "report.pdf")
    return send_file("report.pdf", as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
