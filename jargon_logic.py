# Core logic for Jargon Duel (imported by app.py)
import os
import numpy as np
import json
import random
from dotenv import load_dotenv
import openai

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# --- Phrase Loading ---
def load_phrases(filepath="jargonPhrases.txt"):
    phrases = []
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            phrases = [line.strip() for line in f if line.strip()]
    return phrases

# --- Similarity Matrix ---
SIMILARITY_FILE = "similarity_matrix.json"
def load_similarity_matrix(filepath=SIMILARITY_FILE):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None

def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))

# --- Elo Calculation ---
K_FACTOR = 32
INITIAL_ELO = 1000

def calculate_expected_score(elo_a, elo_b):
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

def update_elo(winner_elo, loser_elo, k=K_FACTOR):
    expected_winner = calculate_expected_score(winner_elo, loser_elo)
    expected_loser = calculate_expected_score(loser_elo, winner_elo)
    new_winner_elo = winner_elo + k * (1 - expected_winner)
    new_loser_elo = loser_elo + k * (0 - expected_loser)
    return round(new_winner_elo), round(new_loser_elo) 