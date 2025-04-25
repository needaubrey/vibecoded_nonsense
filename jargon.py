import os
import openai
import numpy as np
import json
import random
import math
from dotenv import load_dotenv # Use python-dotenv

load_dotenv() # Load environment variables from .env file

# Load API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY not found in environment variables.")
    print("Please create a .env file with OPENAI_API_KEY='your_key'")
    # Decide how to handle this - exit? Or let OpenAI library handle it?
    # For now, let it proceed, OpenAI library might raise its own error.
    # Or uncomment below to exit:
    # import sys
    # sys.exit(1)

# Set the key for the openai library (only if found)
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

ELO_FILE = "elo_scores.json"
INITIAL_ELO = 1000
K_FACTOR = 32 # Elo K-factor determines sensitivity of rating changes

# --- Phrase Loading ---

def load_phrases(filepath="jargonPhrases.txt"):
    """Loads phrases from a file, one per line."""
    phrases = []
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            phrases = [line.strip() for line in f if line.strip()]
    if not phrases:
        print(f"Warning: Could not load phrases from {filepath}. File might be missing or empty.")
    return phrases

# --- Similarity Calculation (kept for potential future use) ---

SIMILARITY_FILE = "similarity_matrix.json"

def save_similarity_matrix(matrix, filepath=SIMILARITY_FILE):
    """Saves the similarity matrix to a JSON file."""
    try:
        with open(filepath, 'w') as f:
            json.dump(matrix, f, indent=4)
        print(f"Similarity matrix saved to {filepath}")
    except IOError as e:
        print(f"Error saving similarity matrix to {filepath}: {e}")

def load_similarity_matrix(filepath=SIMILARITY_FILE):
    """Loads the similarity matrix from a JSON file."""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                matrix = json.load(f)
            print(f"Loaded similarity matrix from {filepath}")
            return matrix
        except json.JSONDecodeError:
            print(f"Warning: Error reading {filepath}. Will recalculate matrix if needed.")
            return None
        except IOError as e:
            print(f"Warning: Could not read {filepath}: {e}. Will recalculate matrix if needed.")
            return None
    else:
        return None

def get_or_calculate_similarity_matrix(phrases):
    """Loads the similarity matrix from file or calculates it if not found/invalid."""
    matrix = load_similarity_matrix()
    
    # Basic validation: Check if the loaded matrix covers the current phrases
    if matrix:
        loaded_phrases = set(matrix.keys())
        current_phrases_set = set(phrases)
        if loaded_phrases == current_phrases_set:
             # Check if inner dictionaries also cover all phrases
             valid = True
             for p1 in matrix:
                 if set(matrix[p1].keys()) != current_phrases_set:
                     valid = False
                     break
             if valid:
                 return matrix
             else:
                 print("Warning: Loaded similarity matrix structure mismatch. Recalculating.")
        else:
            print("Warning: Phrase list changed since similarity matrix was saved. Recalculating.")

    print("Calculating similarity matrix (this requires OpenAI API call and may take time)...")
    # Fallback to calculation if loading failed or matrix is invalid/outdated
    matrix = calculate_similarity_matrix_internal(phrases)
    if matrix: # Save only if calculation was successful
        save_similarity_matrix(matrix)
    return matrix

def calculate_similarity_matrix_internal(phrases):
    """Internal function to calculates the similarity matrix using embeddings."""
    if not phrases:
        return {}
    try:
        response = openai.Embedding.create(
            input=phrases,
            model="text-embedding-3-small"
        )
        embeddings = [d["embedding"] for d in response["data"]]
        phrase_to_embedding = {phrase: emb for phrase, emb in zip(phrases, embeddings)}

        similarity_scores = {phrase_a: {} for phrase_a in phrases}
        for i, phrase_a in enumerate(phrases):
            emb_a = phrase_to_embedding[phrase_a]
            for j, phrase_b in enumerate(phrases):
                emb_b = phrase_to_embedding[phrase_b]
                if phrase_a == phrase_b:
                    similarity_scores[phrase_a][phrase_b] = 1.0
                else:
                    sim = cosine_similarity(emb_a, emb_b)
                    similarity_scores[phrase_a][phrase_b] = sim # Store raw similarity
        print("Similarity matrix calculated.")
        return similarity_scores
    except Exception as e:
        print(f"Error calculating similarity matrix: {e}")
        # Return None if calculation fails
        return None

def cosine_similarity(vec1, vec2):
    """Calculates cosine similarity between two vectors."""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))

# --- Elo Rating System ---

def calculate_expected_score(elo_a, elo_b):
    """Calculates the expected score of player A against player B."""
    return 1 / (1 + math.pow(10, (elo_b - elo_a) / 400))

def update_elo(winner_elo, loser_elo, k=K_FACTOR):
    """Updates Elo ratings based on the winner and loser."""
    expected_winner = calculate_expected_score(winner_elo, loser_elo)
    expected_loser = calculate_expected_score(loser_elo, winner_elo)

    new_winner_elo = winner_elo + k * (1 - expected_winner)
    new_loser_elo = loser_elo + k * (0 - expected_loser)

    return round(new_winner_elo), round(new_loser_elo)

def load_elo_scores(phrases, filepath=ELO_FILE):
    """Loads Elo scores from a file, initializing new phrases."""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                scores = json.load(f)
            # Add any new phrases with initial Elo
            for phrase in phrases:
                if phrase not in scores:
                    scores[phrase] = INITIAL_ELO
            # Remove phrases no longer in the list (optional, keeps file clean)
            current_phrases_set = set(phrases)
            scores_to_remove = [p for p in scores if p not in current_phrases_set]
            for p in scores_to_remove:
                del scores[p]

        except json.JSONDecodeError:
            print(f"Warning: Error reading {filepath}. Initializing all scores.")
            scores = {phrase: INITIAL_ELO for phrase in phrases}
    else:
        print(f"No existing Elo file found at {filepath}. Initializing scores.")
        scores = {phrase: INITIAL_ELO for phrase in phrases}
    return scores

def save_elo_scores(scores, filepath=ELO_FILE):
    """Saves Elo scores to a file."""
    try:
        with open(filepath, 'w') as f:
            json.dump(scores, f, indent=4)
    except IOError as e:
        print(f"Error saving Elo scores to {filepath}: {e}")

# --- Game UI and Logic (CLI versions - kept for reference or potential future use) ---
def display_leaderboard_cli(elo_scores, top_n=10):
    """Displays the top N phrases by Elo score."""
    if not elo_scores:
        print("No scores to display.")
        return
    
    sorted_phrases = sorted(elo_scores.items(), key=lambda item: item[1], reverse=True)
    
    print("\n--- Jargon Leaderboard ---")
    for i, (phrase, score) in enumerate(sorted_phrases[:top_n]):
        print(f"{i+1}. {phrase} (Elo: {score})")
    print("------------------------\n")

def play_round_cli(phrases, elo_scores):
    """Plays a single round of Jargon Duel."""
    if len(phrases) < 2:
        print("Not enough phrases to play.")
        return False # Indicate game cannot continue

    # Select two distinct random phrases
    phrase1, phrase2 = random.sample(phrases, 2)
    elo1 = elo_scores[phrase1]
    elo2 = elo_scores[phrase2]

    print("Which phrase is 'better' (more impactful, useful, etc.)?")
    print(f'1: "{phrase1}" (Current Elo: {elo1})')
    print(f'2: "{phrase2}" (Current Elo: {elo2})')

    choice = ""
    while choice not in ['1', '2']:
        choice = input("Enter your choice (1 or 2): ").strip()
        if choice not in ['1', '2']:
            print("Invalid input. Please enter 1 or 2.")

    if choice == '1':
        winner_phrase, loser_phrase = phrase1, phrase2
        winner_elo_old, loser_elo_old = elo1, elo2
    else:
        winner_phrase, loser_phrase = phrase2, phrase1
        winner_elo_old, loser_elo_old = elo2, elo1

    # Update Elo scores
    winner_elo_new, loser_elo_new = update_elo(winner_elo_old, loser_elo_old)
    elo_scores[winner_phrase] = winner_elo_new
    elo_scores[loser_phrase] = loser_elo_new

    print("\nChoice registered!")
    print(f'"{winner_phrase}" Elo: {winner_elo_old} -> {winner_elo_new} ({winner_elo_new - winner_elo_old:+})')
    print(f'"{loser_phrase}" Elo: {loser_elo_old} -> {loser_elo_new} ({loser_elo_new - loser_elo_old:+})')

    # Save scores after each round
    save_elo_scores(elo_scores)
    return True # Indicate round was played successfully

def game_loop_cli(phrases, elo_scores):
    """Main game loop for Jargon Duel."""
    if not phrases:
         print("Cannot start game without phrases.")
         return

    while True:
        display_leaderboard_cli(elo_scores)
        if not play_round_cli(phrases, elo_scores):
            break # Stop if play_round indicates an issue

        play_again = input("Play another round? (y/n): ").strip().lower()
        if play_again != 'y':
            break

    print("Thanks for playing Jargon Duel!")
    display_leaderboard_cli(elo_scores) # Show final leaderboard

# --- Main Execution (Removed for GUI) ---

# if __name__ == "__main__":
#     print("Welcome to Jargon Duel! (CLI Version)")
#     phrases_list = load_phrases()
#     elo_scores_dict = load_elo_scores(phrases_list)
#     game_loop_cli(phrases_list, elo_scores_dict)

        