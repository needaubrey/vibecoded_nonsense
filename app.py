import eventlet
eventlet.monkey_patch()

# --- ALL OTHER IMPORTS GO BELOW ---
import os
import random
import jargon_logic # Assuming this contains load_phrases, load_similarity_matrix, update_elo, INITIAL_ELO
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy

# --- Flask App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_default_secret_key_for_dev') # Use env var or default
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///elo_scores.db'
db = SQLAlchemy(app)
socketio = SocketIO(app, async_mode='eventlet')

# --- Database Model ---
class PhraseElo(db.Model):
    phrase = db.Column(db.String, primary_key=True)
    elo = db.Column(db.Integer, default=jargon_logic.INITIAL_ELO)

# --- Load Data on Startup ---
PHRASES = jargon_logic.load_phrases()
SIMILARITY_MATRIX = jargon_logic.load_similarity_matrix()

# --- Ensure all phrases are in DB ---
with app.app_context():
    db.create_all()
    for phrase in PHRASES:
        if not PhraseElo.query.get(phrase):
            db.session.add(PhraseElo(phrase=phrase, elo=jargon_logic.INITIAL_ELO))
    db.session.commit()

def get_leaderboard(top_n=200):
    return PhraseElo.query.order_by(PhraseElo.elo.desc()).limit(top_n).all()

def get_weighted_pair():
    phrase1 = random.choice(PHRASES)
    similarities = SIMILARITY_MATRIX[phrase1]
    other_phrases = []
    weights = []
    similarity_exponent = 3
    for phrase, score in similarities.items():
        if phrase != phrase1:
            scaled_score = (score + 1) / 2
            weight = (scaled_score + 1e-9) ** similarity_exponent
            other_phrases.append(phrase)
            weights.append(weight)
    if not other_phrases or sum(weights) <= 1e-9:
        phrase2 = random.choice([p for p in PHRASES if p != phrase1])
    else:
        phrase2 = random.choices(other_phrases, weights=weights, k=1)[0]
    return phrase1, phrase2

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')

# Debug route for 403 troubleshooting
@app.route('/test')
def test():
    return "Test OK"

# --- SocketIO Events ---
@socketio.on('request_pair')
def handle_request_pair():
    phrase1, phrase2 = get_weighted_pair()
    emit('new_pair', {'phrase1': phrase1, 'phrase2': phrase2})

@socketio.on('vote')
def handle_vote(data):
    winner = data['winner']
    loser = data['loser']
    winner_row = PhraseElo.query.get(winner)
    loser_row = PhraseElo.query.get(loser)
    if winner_row and loser_row:
        winner_elo_new, loser_elo_new = jargon_logic.update_elo(winner_row.elo, loser_row.elo)
        winner_row.elo = winner_elo_new
        loser_row.elo = loser_elo_new
        db.session.commit()
        # Broadcast updated leaderboard to all
        leaderboard = get_leaderboard()
        emit('leaderboard_update',
             {'leaderboard': [[row.phrase, row.elo] for row in leaderboard]},
             broadcast=True)
    # Send new pair to the voting user
    phrase1, phrase2 = get_weighted_pair()
    emit('new_pair', {'phrase1': phrase1, 'phrase2': phrase2})

@socketio.on('request_leaderboard')
def handle_request_leaderboard():
    leaderboard = get_leaderboard()
    emit('leaderboard_update',
         {'leaderboard': [[row.phrase, row.elo] for row in leaderboard]})

if __name__ == '__main__':
    socketio.run(app, debug=True) 