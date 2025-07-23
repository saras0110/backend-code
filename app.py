from flask import Flask, render_template, request, redirect, url_for, session
import json
import uuid 
from werkzeug.utils import secure_filename
import os
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "supersecretkey"
CORS(app)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ----------------------- Utilities ----------------------------

def load_json(filename):
    if not os.path.exists(filename):
        if filename == 'countdowns.json':
            with open(filename, 'w') as f:
                json.dump({
                    "candidate_registration": {"start": "", "end": ""},
                    "voter_registration": {"start": "", "end": ""},
                    "voting": {"start": "", "end": ""}
                }, f)
        else:
            with open(filename, 'w') as f:
                json.dump([], f)
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
        result[party] = result.get(party, 0) + 1
    return result

# ----------------------- Main Pages ----------------------------

@app.route('/')
def index():
    countdowns = load_json('countdowns.json')
    return render_template('index.html', countdowns=countdowns)

@app.route('/role_select')
def role_select():
    return render_template('role_select.html')

# ----------------------- Voter ----------------------------

@app.route('/voter_register_page')
def voter_register_page():
    return render_template('voter_register.html')

@app.route('/voter_login_page')
def voter_login_page():
    return render_template('voter_login.html')

@app.route('/voter_register', methods=['POST'])
def voter_register():
    voters = load_json('voters.json')
    new_voter = {
        "name": request.form['name'],
        "year": request.form['year'],
        "age": request.form['age'],
        "gender": request.form['gender'],
        "username": request.form['username'],
        "password": request.form['password']
    }
    voters.append(new_voter)
    save_json('voters.json', voters)
    return redirect(url_for('voter_login_page'))

@app.route('/voter_login', methods=['POST'])
def voter_login():
    voters = load_json('voters.json')
    username = request.form['username']
    password = request.form['password']
    for v in voters:
        if v['username'] == username and v['password'] == password:
            session['voter'] = username
            return redirect(url_for('voter_dashboard'))
    return render_template('voter_login.html', msg="Invalid credentials!")

@app.route('/voter_dashboard')
def voter_dashboard():
    if 'voter' not in session:
        return redirect(url_for('voter_login_page'))
    candidates = load_json('candidates.json')
    return render_template('voter_dashboard.html', candidates=candidates)

@app.route('/vote/<party>')
def vote(party):
    if 'voter' not in session:
        return redirect(url_for('voter_login_page'))
    votes = load_json('votes.json')
    username = session['voter']
    votes = [v for v in votes if v['voter'] != username]
    votes.append({"voter": username, "party": party})
    save_json('votes.json', votes)
    return redirect(url_for('voter_dashboard'))

# ----------------------- Candidate ----------------------------

@app.route('/candidate_register_page')
def candidate_register_page():
    return render_template('candidate_register.html')

@app.route('/candidate_login_page')
def candidate_login_page():
    return render_template('candidate_login.html')

@app.route('/candidate_register', methods=['POST'])
def candidate_register():
    candidates = load_json('candidates.json')
     # get file
    if 'party_logo' not in request.files:
        return "No file uploaded", 400

    file = request.files['party_logo']
    if file.filename == '':
        return "No selected file", 400

    # secure filename
    filename = secure_filename(file.filename)
    unique_filename = str(uuid.uuid4()) + "_" + filename
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
    new_candidate = {
        "name": request.form['name'],
        "party_name": request.form['party_name'],
        "moto": request.form['party_moto'],
        "year": request.form['year'],
        "age": request.form['age'],
        "gender": request.form['gender'],
        "username": request.form['username'],
        "password": request.form['password'],
        "logo": unique_filename,  # store filename
        "banned": False
    }
    candidates.append(new_candidate)
    save_json('candidates.json', candidates)
    return redirect(url_for('candidate_login_page'))

@app.route('/candidate_login', methods=['POST'])
def candidate_login():
    candidates = load_json('candidates.json')
    username = request.form['username']
    password = request.form['password']
    for c in candidates:
        if c['username'] == username and c['password'] == password:
            session['candidate'] = username
            return redirect(url_for('candidate_dashboard'))
    return render_template('candidate_login.html', msg="Invalid credentials!")

@app.route('/candidate_dashboard')
def candidate_dashboard():
    if 'candidate' not in session:
        return redirect(url_for('candidate_login_page'))
    candidates = load_json('candidates.json')
    votes = get_current_votes()
    user = next((c for c in candidates if c['username'] == session['candidate']), None)
    vote_count = votes.get(user['party_name'], 0) if user else 0
    return render_template('candidate_dashboard.html', candidate=user, votes=vote_count)

# ----------------------- Admin ----------------------------

@app.route('/admin_login_page')
def admin_login_page():
    return render_template('admin_login.html')

@app.route('/admin_login', methods=['POST'])
def admin_login():
    admins = load_json('admin.json')
    username = request.form['username']
    password = request.form['password']
    for a in admins:
        if a['username'] == username and a['password'] == password:
            session['admin'] = username
            return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html', msg="Invalid credentials!")

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login_page'))
    candidates = load_json('candidates.json')
    voters = load_json('voters.json')
    countdowns = load_json('countdowns.json')
    votes = get_current_votes()
    return render_template('admin_dashboard.html', candidates=candidates, voters=voters, countdowns=countdowns, votes=votes)

@app.route('/set_countdown', methods=['POST'])
def set_countdown():
    if 'admin' not in session:
        return redirect(url_for('admin_login_page'))
    countdowns = {
        "candidate_registration": {"start": request.form['cand_start'], "end": request.form['cand_end']},
        "voter_registration": {"start": request.form['voter_start'], "end": request.form['voter_end']},
        "voting": {"start": request.form['voting_start'], "end": request.form['voting_end']}
    }
    save_json('countdowns.json', countdowns)
    return redirect(url_for('admin_dashboard'))

@app.route('/ban_candidate', methods=['POST'])
def ban_candidate():
    if 'admin' not in session:
        return redirect(url_for('admin_login_page'))
    username = request.form['candidate_username']
    candidates = load_json('candidates.json')
    for c in candidates:
        if c['username'] == username:
            c['banned'] = True
    save_json('candidates.json', candidates)
    return redirect(url_for('admin_dashboard'))

@app.route('/unban_candidate', methods=['POST'])
def unban_candidate():
    if 'admin' not in session:
        return redirect(url_for('admin_login_page'))
    username = request.form['candidate_username']
    candidates = load_json('candidates.json')
    for c in candidates:
        if c['username'] == username:
            c['banned'] = False
    save_json('candidates.json', candidates)
    return redirect(url_for('admin_dashboard'))

@app.route('/live_result')
def live_result():
    votes = get_current_votes()
    return render_template('live_result.html', votes=votes)

# ----------------------- Run ----------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # default fallback port
    app.run(host='0.0.0.0', port=port)


