import tkinter as tk
from tkinter import ttk, messagebox, Scrollbar # Added Scrollbar
import random
import math # Added math for exponentiation
import jargon # Import the logic from jargon.py

class JargonDuelApp:
    def __init__(self, master):
        self.master = master
        master.title("Jargon Duel")
        # Increased height further for larger leaderboard
        master.geometry("600x600") 

        # Load data
        self.phrases = jargon.load_phrases()
        if not self.phrases or len(self.phrases) < 2:
            messagebox.showerror("Error", "Could not load sufficient phrases from jargonPhrases.txt. Exiting.")
            master.quit()
            return
            
        self.elo_scores = jargon.load_elo_scores(self.phrases)
        
        # --- Get Similarity Matrix (Load or Calculate) ---
        # This might take time and cost API credits on first run!
        self.status_label = ttk.Label(master, text="Loading/Calculating Similarity Matrix...")
        self.status_label.pack(pady=5)
        master.update_idletasks() # Update UI to show status message
        
        self.similarity_matrix = jargon.get_or_calculate_similarity_matrix(self.phrases)
        if self.similarity_matrix is None:
             messagebox.showerror("Error", "Failed to load or calculate similarity matrix. Cannot use weighted selection.")
             # Fallback to purely random?
             # For now, just exit if calculation fails and no file exists
             master.quit()
             return
        self.status_label.config(text="Similarity Matrix Ready.") # Update status
        self.status_label.pack_forget() # Hide status after loading

        # Style
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Helvetica', 12), padding=10)
        self.style.configure('TLabel', font=('Helvetica', 14), padding=10)
        self.style.configure('Header.TLabel', font=('Helvetica', 16, 'bold'))

        # --- UI Elements ---
        self.header_label = ttk.Label(master, text="Which Jargon is Better?", style='Header.TLabel')
        self.header_label.pack(pady=10)

        # Frame for the duel options
        self.duel_frame = ttk.Frame(master)
        self.duel_frame.pack(pady=20, fill=tk.X, padx=20)

        self.phrase1_label = ttk.Label(self.duel_frame, text="", wraplength=250, justify=tk.CENTER)
        self.phrase1_button = ttk.Button(self.duel_frame, text="This One!", command=lambda: self.choose_winner(1))
        
        self.phrase2_label = ttk.Label(self.duel_frame, text="", wraplength=250, justify=tk.CENTER)
        self.phrase2_button = ttk.Button(self.duel_frame, text="This One!", command=lambda: self.choose_winner(2))

        # Layout duel options side-by-side
        self.phrase1_label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.phrase1_button.grid(row=1, column=0, padx=10, pady=10)
        ttk.Label(self.duel_frame, text="vs").grid(row=0, column=1, rowspan=2, padx=10)
        self.phrase2_label.grid(row=0, column=2, padx=10, pady=5, sticky="ew")
        self.phrase2_button.grid(row=1, column=2, padx=10, pady=10)
        
        self.duel_frame.columnconfigure(0, weight=1)
        self.duel_frame.columnconfigure(1, weight=0) # VS label column
        self.duel_frame.columnconfigure(2, weight=1)

        # --- Leaderboard Frame with Scrollbar ---
        self.leaderboard_frame = ttk.Frame(master)
        self.leaderboard_frame.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)

        self.leaderboard_label = ttk.Label(self.leaderboard_frame, text="Leaderboard (Top 200)")
        self.leaderboard_label.pack(pady=(5,0))

        self.leaderboard_scrollbar = Scrollbar(self.leaderboard_frame, orient=tk.VERTICAL)
        self.leaderboard_text = tk.Text(self.leaderboard_frame,
                                         height=15, # Adjusted height
                                         width=60,
                                         wrap=tk.WORD,
                                         state=tk.DISABLED,
                                         font=('Courier', 11),
                                         yscrollcommand=self.leaderboard_scrollbar.set)
        self.leaderboard_scrollbar.config(command=self.leaderboard_text.yview)
        
        self.leaderboard_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.leaderboard_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Store current duel phrases
        self.current_phrase1 = None
        self.current_phrase2 = None

        # Start the first round
        self.next_round()
        self.update_leaderboard()

    def next_round(self):
        """Selects the next pair of phrases, biased strongly by similarity."""
        if not self.similarity_matrix:
            messagebox.showerror("Error", "Similarity matrix not available.")
            return
            
        # 1. Pick the first phrase randomly
        self.current_phrase1 = random.choice(self.phrases)

        # 2. Get similarities of phrase1 to all other phrases
        similarities = self.similarity_matrix[self.current_phrase1]
        
        # 3. Prepare lists for weighted random choice (excluding phrase1 itself)
        other_phrases = []
        weights = []
        similarity_exponent = 3 # Adjust this exponent to change bias strength (higher = stronger bias)

        for phrase, score in similarities.items():
            if phrase != self.current_phrase1:
                other_phrases.append(phrase)
                # Scale score from [-1, 1] to [0, 1]
                scaled_score = (score + 1) / 2
                # Apply exponent to increase bias towards higher scores
                # Add small epsilon to avoid issues with 0^exponent if exponent isn't integer > 0
                weight = (scaled_score + 1e-9) ** similarity_exponent 
                weights.append(weight)

        # Check if there are valid weights/phrases left
        if not other_phrases or sum(weights) <= 1e-9: # Use epsilon for sum check
             # Fallback to purely random selection if no valid weights
             print("Warning: No valid similarity weights found. Falling back to random.")
             possible_phrases = [p for p in self.phrases if p != self.current_phrase1]
             if not possible_phrases:
                  messagebox.showerror("Error", "Cannot select a second distinct phrase.")
                  self.master.quit()
                  return
             self.current_phrase2 = random.choice(possible_phrases)
        else:
            # 4. Choose the second phrase using weighted random selection
            self.current_phrase2 = random.choices(other_phrases, weights=weights, k=1)[0]
        
        # Update labels
        self.phrase1_label.config(text=self.current_phrase1)
        self.phrase2_label.config(text=self.current_phrase2)

    def choose_winner(self, choice):
        if not self.current_phrase1 or not self.current_phrase2:
            return # Should not happen if initialized correctly

        if choice == 1:
            winner_phrase = self.current_phrase1
            loser_phrase = self.current_phrase2
        else:
            winner_phrase = self.current_phrase2
            loser_phrase = self.current_phrase1
            
        elo_winner_old = self.elo_scores[winner_phrase]
        elo_loser_old = self.elo_scores[loser_phrase]

        # Update Elo
        elo_winner_new, elo_loser_new = jargon.update_elo(elo_winner_old, elo_loser_old)
        self.elo_scores[winner_phrase] = elo_winner_new
        self.elo_scores[loser_phrase] = elo_loser_new
        
        # Save scores
        jargon.save_elo_scores(self.elo_scores)
        
        # Update leaderboard display
        self.update_leaderboard()
        
        # Start next round
        self.next_round()

    def update_leaderboard(self, top_n=200): # Changed default top_n to 200
        self.leaderboard_text.config(state=tk.NORMAL)
        self.leaderboard_text.delete('1.0', tk.END)
        
        if not self.elo_scores:
            self.leaderboard_text.insert(tk.END, "No scores yet.")
        else:
            sorted_phrases = sorted(self.elo_scores.items(), key=lambda item: item[1], reverse=True)
            # Display up to top_n entries
            for i, (phrase, score) in enumerate(sorted_phrases[:top_n]):
                self.leaderboard_text.insert(tk.END, f"{i+1:<4} {phrase:<45} (Elo: {score})\n") # Adjusted padding for rank
                
        self.leaderboard_text.config(state=tk.DISABLED)

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = JargonDuelApp(root)
    root.mainloop() 