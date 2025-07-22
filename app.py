from flask import Flask, render_template, request, redirect, session, url_for
import json
import os
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "supersecretkey"
CORS(app)

# ----------------------- Utilities ----------------------------

def load_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def get_current_votes():
    votes = load_json('votes.json')
    result = {}
    for vote in votes:
        party = vote['party']
        if party in result:
            result[party] += 1
        else:
            result[party] = 1
    return result

# ----------------------- Home ----------------------------

@app.route('/')
def home():
    return render_template('index.html')

# ----------------------- Voter ----------------------------

@app.route('/voter_register', methods=['POST'])
def voter_register():
    voters = load_json('voters.json')
    new_voter = {
        "name": request.form['name'],
        "age": request.form['age'],
        "year": request.form['year'],
        "gender": request.form['gender'],
        "username": request.form['username'],
        "password": request.form['password'],
        "profile": request.form['profile']
    }
    voters.append(new_voter)
    save_json('voters.json', voters)
    return render_template('voter_register_login.html', msg="Registered Successfully!")

@app.route('/voter_login', methods=['POST'])
def voter_login():
    voters = load_json('voters.json')
    username = request.form['username']
    password = request.form['password']
    for v in voters:
        if v['username'] == username and v['password'] == password:
            session['voter'] = username
            return redirect('/voter_dashboard')
    return render_template('voter_register_login.html', msg="Invalid credentials!")

@app.route('/voter_dashboard')
def voter_dashboard():
    if 'voter' not in session:
        return redirect('/')
    candidates = load_json('candidates.json')
    return render_template('voter_dashboard.html', candidates=candidates)

@app.route('/vote/<party>')
def vote(party):
    if 'voter' not in session:
        return redirect('/')
    votes = load_json('votes.json')
    username = session['voter']
    votes = [v for v in votes if v['voter'] != username]
    votes.append({"voter": username, "party": party})
    save_json('votes.json', votes)
    return redirect('/voter_dashboard')

# ----------------------- Candidate ----------------------------

@app.route('/candidate_register', methods=['POST'])
def candidate_register():
    candidates = load_json('candidates.json')
    new_candidate = {
        "name": request.form['name'],
        "party_name": request.form['party_name'],
        "moto": request.form['moto'],
        "logo": request.form['logo'],
        "year": request.form['year'],
        "age": request.form['age'],
        "gender": request.form['gender'],
        "username": request.form['username'],
        "password": request.form['password']
    }
    candidates.append(new_candidate)
    save_json('candidates.json', candidates)
    return render_template('candidate_register_login.html', msg="Registered Successfully!")

@app.route('/candidate_login', methods=['POST'])
def candidate_login():
    candidates = load_json('candidates.json')
    username = request.form['username']
    password = request.form['password']
    for c in candidates:
        if c['username'] == username and c['password'] == password:
            session['candidate'] = username
            return redirect('/candidate_dashboard')
    return render_template('candidate_register_login.html', msg="Invalid credentials!")

@app.route('/candidate_dashboard')
def candidate_dashboard():
    if 'candidate' not in session:
        return redirect('/')
    candidates = load_json('candidates.json')
    user = None
    votes = get_current_votes()
    for c in candidates:
        if c['username'] == session['candidate']:
            user = c
            break
    vote_count = votes.get(user['party_name'], 0)
    return render_template('candidate_dashboard.html', candidate=user, votes=vote_count)

# ----------------------- Admin ----------------------------

@app.route('/admin_login', methods=['POST'])
def admin_login():
    admins = load_json('admin.json')
    username = request.form['username']
    password = request.form['password']
    for a in admins:
        if a['username'] == username and a['password'] == password:
            session['admin'] = username
            return redirect('/admin_dashboard')
    return render_template('admin_login.html', msg="Invalid credentials!")

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/')
    candidates = load_json('candidates.json')
    voters = load_json('voters.json')
    countdown = load_json('countdown.json')
    votes = get_current_votes()
    return render_template('admin_dashboard.html', candidates=candidates, voters=voters, countdown=countdown, votes=votes)

@app.route('/set_countdown', methods=['POST'])
def set_countdown():
    if 'admin' not in session:
        return redirect('/')
    countdown = {
        "candidate_registration": {
            "start": request.form['cand_start'],
            "end": request.form['cand_end']
        },
        "voter_registration": {
            "start": request.form['voter_start'],
            "end": request.form['voter_end']
        },
        "voting": {
            "start": request.form['voting_start'],
            "end": request.form['voting_end']
        }
    }
    save_json('countdown.json', countdown)
    return redirect('/admin_dashboard')

@app.route('/clear_data')
def clear_data():
    if 'admin' not in session:
        return redirect('/')
    save_json('candidates.json', [])
    save_json('voters.json', [])
    save_json('votes.json', [])
    return redirect('/admin_dashboard')

@app.route('/live_result')
def live_result():
    votes = get_current_votes()
    return render_template('live_result.html', votes=votes)

# ----------------------- Run ----------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
