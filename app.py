from flask import Flask, render_template, request, redirect, session, send_file
import json
import os
from datetime import datetime
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'secret-key'

# Load JSON files
def load_json(file):
    if os.path.exists(file):
        with open(file) as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

# Load data
users = load_json('users.json')
candidates = load_json('candidates.json')
votes = load_json('votes.json')
countdowns = load_json('countdowns.json')
ADMIN = load_json('admin.json')

# Homepage
@app.route('/')
def index():
    return render_template('index.html')

# Voter Register/Login
@app.route('/voter', methods=['GET', 'POST'])
def voter():
    if request.method == 'POST':
        action = request.form['action']
        if action == 'register':
            username = request.form['username']
            password = request.form['password']
            age = request.form['age']
            gender = request.form['gender']
            year = request.form['year']
            if username in users:
                return "User already exists!"
            users[username] = {'password': password, 'age': age, 'gender': gender, 'year': year, 'voted': False}
            save_json('users.json', users)
            return "Registered successfully! Now log in."
        elif action == 'login':
            username = request.form['username']
            password = request.form['password']
            user = users.get(username)
            if user and user['password'] == password:
                session['voter'] = username
                return redirect('/voter_dashboard')
            return "Invalid credentials!"
    return render_template('voter_register_login.html')

# Voter Dashboard
@app.route('/voter_dashboard')
def voter_dashboard():
    if 'voter' not in session:
        return redirect('/voter')
    voter = session['voter']
    user = users[voter]
    voted = user['voted']
    return render_template('voter_dashboard.html', candidates=candidates, voted=voted)

# Vote
@app.route('/vote/<candidate>')
def vote(candidate):
    if 'voter' not in session:
        return redirect('/voter')
    voter = session['voter']
    if users[voter]['voted']:
        return "Already voted!"
    # Check voting deadline
    if countdowns['voting_end']:
        voting_deadline = datetime.fromisoformat(countdowns['voting_end'])
        if datetime.now() > voting_deadline:
            return "Voting period ended!"
    votes.setdefault(candidate, 0)
    votes[candidate] += 1
    users[voter]['voted'] = True
    save_json('votes.json', votes)
    save_json('users.json', users)
    return "Vote cast successfully!"

# Candidate Register/Login
@app.route('/candidate', methods=['GET', 'POST'])
def candidate():
    if request.method == 'POST':
        action = request.form['action']
        if action == 'register':
            username = request.form['username']
            password = request.form['password']
            name = request.form['name']
            year = request.form['year']
            age = request.form['age']
            gender = request.form['gender']
            party = request.form['party']
            motto = request.form['motto']
            if username in candidates:
                return "Candidate exists!"
            candidates[username] = {
                'password': password, 'name': name, 'year': year,
                'age': age, 'gender': gender, 'party': party, 'motto': motto
            }
            save_json('candidates.json', candidates)
            return "Registered successfully! Now log in."
        elif action == 'login':
            username = request.form['username']
            password = request.form['password']
            user = candidates.get(username)
            if user and user['password'] == password:
                session['candidate'] = username
                return redirect('/candidate_dashboard')
            return "Invalid credentials!"
    return render_template('candidate_register_login.html')

# Candidate Dashboard
@app.route('/candidate_dashboard', methods=['GET', 'POST'])
def candidate_dashboard():
    if 'candidate' not in session:
        return redirect('/candidate')
    username = session['candidate']
    candidate = candidates[username]
    if request.method == 'POST':
        # Candidate can update details before deadline
        if countdowns['candidate_reg_end']:
            reg_deadline = datetime.fromisoformat(countdowns['candidate_reg_end'])
            if datetime.now() > reg_deadline:
                return "Registration edit closed!"
        candidate['motto'] = request.form['motto']
        candidate['party'] = request.form['party']
        save_json('candidates.json', candidates)
        return "Updated!"
    return render_template('candidate_dashboard.html', candidate=candidate)

# Admin Login
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN['username'] and password == ADMIN['password']:
            session['admin'] = True
            return redirect('/admin_dashboard')
        return "Invalid admin!"
    return render_template('admin_login.html')

# Admin Dashboard
@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin')
    if request.method == 'POST':
        candidate_reg_end = request.form['candidate_reg_end']
        voting_end = request.form['voting_end']
        countdowns['candidate_reg_end'] = candidate_reg_end
        countdowns['voting_end'] = voting_end
        save_json('countdowns.json', countdowns)
    return render_template('admin_dashboard.html',
                           candidates=candidates,
                           votes=votes,
                           countdowns=countdowns)

# Generate PDF
@app.route('/generate_pdf')
def generate_pdf():
    if 'admin' not in session:
        return redirect('/admin')
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Voting Results", ln=True, align='C')
    for candidate, count in votes.items():
        pdf.cell(200, 10, txt=f"{candidate}: {count} votes", ln=True)
    pdf.output("results.pdf")
    return send_file("results.pdf", as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
