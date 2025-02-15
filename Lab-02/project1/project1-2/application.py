import os
from flask import Flask, render_template, request, redirect, session, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import bcrypt

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database connection using SQLAlchemy
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Function to create the users table if it doesn't exist
def create_tables():
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    """)
    db.commit()
    print("Users table created (if it didn't exist).")

@app.route("/")
def index():
    return render_template("index.html")



if __name__ == "__main__":
    create_tables()  # Ensure table exists before running the app
    app.run(debug=True)
