# Jargon Duel

A simple web application to rank corporate jargon phrases.

Pick which corporate jargon phrase you like better! The leaderboard tracks the most popular picks!

## Features

*   Real-time voting using Flask-SocketIO.
*   Elo rating system to rank phrases based on votes.
*   Weighted pairing attempts to show similarly ranked phrases (requires `similarity_matrix.json`).
*   PostgreSQL database backend for storing Elo scores.
*   Leaderboard to view top-ranked phrases.

## Technologies Used

*   Python
*   Flask
*   Flask-SocketIO
*   Flask-SQLAlchemy
*   Eventlet
*   Gunicorn
*   psycopg2 (PostgreSQL driver)
*   PostgreSQL
*   HTML, CSS, JavaScript

## Setup and Running Locally

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd jargon
    ```

2.  **Create a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Database Setup:**
    *   The application uses PostgreSQL.
    *   By default, for local development against a deployed DB (like Render), it expects the connection URL in an environment variable named `DATABASE_URL` (which `python-dotenv` can load from a `.env` file if present).
    *   If `DATABASE_URL` is not set, it will fall back to the SQLite file `elo_scores.db` (ensure this file is in your `.gitignore`).
    *   Example `.env` file for connecting to a local Postgres DB:
        ```
        DATABASE_URL=postgresql://user:password@localhost:5432/jargon_db
        SECRET_KEY=yoursecretflaskkey
        ```

5.  **Run the application:**
    ```bash
    python app.py
    ```
    The app should be accessible at `http://localhost:5050` (or `http://0.0.0.0:5050`).

## Deployment (Render Example)

*   **Build Command:** `pip install -r requirements.txt`
*   **Start Command:** `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app`
*   **Environment Variables:**
    *   `DATABASE_URL`: Render usually injects this automatically when linking a database service.
    *   `SECRET_KEY`: Set a strong, random secret key.
    *   `PYTHON_VERSION`: (Optional) e.g., `3.11.11`
*   **Similarity Matrix:** If you want weighted pairing, ensure `similarity_matrix.json` is *not* in `.gitignore` and is committed to the repository. 