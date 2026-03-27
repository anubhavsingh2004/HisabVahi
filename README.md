# HisabVahi

HisabVahi is a minimal full-stack Flask web application to track:
- Cash inflow
- Cash outflow
- Udhari (credit/debit ledger)

This project is beginner-friendly and designed for learning Python full stack development with Flask, SQLAlchemy, SQLite, Jinja2, and Bootstrap.

## Tech Stack

Backend:
- Python
- Flask
- SQLAlchemy ORM
- SQLite

Frontend:
- HTML
- Bootstrap 5
- Jinja2 templates
- Minimal JavaScript

Authentication:
- Session-based login
- Password hashing using Werkzeug

## Features

### 1) Authentication
- Register
- Login
- Logout
- Route protection using session-based auth

User fields:
- id
- username
- email
- password_hash
- created_at

### 2) Dashboard
- Total Cash In
- Total Cash Out
- Total Receivable
- Total Payable
- Recent transactions

### 3) Party Management
- Add party
- View parties list
- Edit party
- Delete party
- Current balance per party

Party fields:
- id
- name
- phone
- party_type (customer, supplier, friend, other)
- notes
- created_at

### 4) Transaction Management
- Add transaction
- View transactions
- Edit transaction
- Delete transaction

Transaction fields:
- id
- party_id (optional)
- transaction_type
- amount
- description
- date
- created_at

Transaction types:
- cash_in
- cash_out
- udhari_given
- udhari_taken
- repayment_received
- repayment_paid

### 5) Ledger (Person-wise)
For each party:
- Full transaction history
- Total receivable
- Total payable
- Net balance

Formulas:
- Receivable = sum(udhari_given) - sum(repayment_received)
- Payable = sum(udhari_taken) - sum(repayment_paid)
- Net Balance = Receivable - Payable

Meaning:
- Positive net balance: person owes money to you
- Negative net balance: you owe money to person
- Zero: settled

## Project Structure

<project-folder>/
- app.py
- models.py
- config.py
- requirements.txt
- database.db
- README.md
- templates/
  - base.html
  - login.html
  - register.html
  - dashboard.html
  - parties.html
  - add_party.html
  - transactions.html
  - add_transaction.html
  - ledger.html
- static/
  - css/
    - style.css
  - js/
    - app.js

## Setup Instructions (Windows PowerShell)

1. Open terminal in project folder:

   cd D:\path\to\<project-folder>

2. Create a virtual environment:

   py -m venv .venv

3. Activate virtual environment:

   .\.venv\Scripts\Activate.ps1

4. Install dependencies:

   pip install -r requirements.txt

## Database Initialization

The app auto-creates database tables on startup using SQLAlchemy `db.create_all()`.

SQLite database file is:
- database.db

## Run the App

Start Flask app:

python app.py

Then open in browser:

http://127.0.0.1:5000

## Default Navigation

After login, top navbar includes:
- Dashboard
- Parties
- Transactions
- Add Transaction
- Logout

## Notes for Learners

- This project uses simple route-based architecture in a single app file for easier understanding.
- Forms include basic validation and flash messages.
- You can expand this project with search, CSV export, and reports.

## Requirements

See requirements.txt:
- Flask
- Flask-SQLAlchemy
- Werkzeug

## License

This project is for learning and personal use.
