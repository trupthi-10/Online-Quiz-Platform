Online Quiz Platform

This is a Flask-based online quiz platform where users can register, log in, attempt quizzes, view their score, and check the leaderboard. Each question has a 60 second timer and questions appear in random order for every attempt.

Features

Home page with details and navigation

User registration and login

Quiz with random questions and 60 second timer

Prevents submission without selecting an option

Score calculation at the end

Leaderboard with previous attempts and scores

SQLite database for storing data

Tech Stack

Backend Flask
Frontend HTML CSS Bootstrap Jinja2
Database SQLite

How to Run

Clone the repository

Create and activate a virtual environment

Install dependencies using pip install -r requirements.txt

Run the application with python app.py

Open http://127.0.0.1:5000/
 in your browser

Database

The application uses SQLite. A quiz.db file will be created automatically with users questions and scores tables.
