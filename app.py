from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models import Party, Transaction, User, db


TRANSACTION_TYPES = {
    "cash_in": "Cash In",
    "cash_out": "Cash Out",
    "udhari_given": "Udhari Given",
    "udhari_taken": "Udhari Taken",
    "repayment_received": "Repayment Received",
    "repayment_paid": "Repayment Paid",
}

PARTY_TYPES = ["customer", "supplier", "friend", "other"]


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


# Create tables at startup for beginner-friendly local setup.
with app.app_context():
    db.create_all()


def login_required(view_func):
    """Protect routes that require login."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


@app.before_request
def load_logged_in_user():
    """Load user object from session for each request."""
    user_id = session.get("user_id")
    g.user = User.query.get(user_id) if user_id else None


def get_sum(transactions, tx_type):
    return sum(t.amount for t in transactions if t.transaction_type == tx_type)


def calculate_receivable_payable(transactions):
    receivable = get_sum(transactions, "udhari_given") - get_sum(
        transactions, "repayment_received"
    )
    payable = get_sum(transactions, "udhari_taken") - get_sum(
        transactions, "repayment_paid"
    )
    return receivable, payable


def parse_amount(raw_amount):
    """Validate and parse amount safely."""
    try:
        amount = float(raw_amount)
        if amount <= 0:
            return None
        return round(amount, 2)
    except (TypeError, ValueError):
        return None


def parse_date(raw_date):
    """Validate and parse date safely."""
    try:
        return datetime.strptime(raw_date, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


@app.route("/")
def index():
    if g.user:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("Username is already taken.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Email is already registered.", "danger")
            return render_template("register.html")

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html")

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user.id
        flash(f"Welcome, {user.username}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    transactions = Transaction.query.filter_by(user_id=g.user.id).all()

    total_cash_in = get_sum(transactions, "cash_in")
    total_cash_out = get_sum(transactions, "cash_out")
    total_receivable, total_payable = calculate_receivable_payable(transactions)

    recent_transactions = (
        Transaction.query.filter_by(user_id=g.user.id)
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "dashboard.html",
        total_cash_in=total_cash_in,
        total_cash_out=total_cash_out,
        total_receivable=total_receivable,
        total_payable=total_payable,
        recent_transactions=recent_transactions,
        transaction_types=TRANSACTION_TYPES,
    )


@app.route("/parties")
@login_required
def parties():
    parties_list = Party.query.filter_by(user_id=g.user.id).order_by(Party.name.asc()).all()
    party_balances = {}

    for party in parties_list:
        receivable, payable = calculate_receivable_payable(party.transactions)
        party_balances[party.id] = receivable - payable

    return render_template(
        "parties.html",
        parties=parties_list,
        party_balances=party_balances,
    )


@app.route("/parties/add", methods=["GET", "POST"])
@login_required
def add_party():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        party_type = request.form.get("party_type", "other").strip().lower()
        notes = request.form.get("notes", "").strip()

        if not name:
            flash("Party name is required.", "danger")
            return render_template(
                "add_party.html",
                party_types=PARTY_TYPES,
                form_data=request.form,
                edit_mode=False,
            )

        if party_type not in PARTY_TYPES:
            flash("Invalid party type.", "danger")
            return render_template(
                "add_party.html",
                party_types=PARTY_TYPES,
                form_data=request.form,
                edit_mode=False,
            )

        party = Party(
            user_id=g.user.id,
            name=name,
            phone=phone,
            party_type=party_type,
            notes=notes,
        )
        db.session.add(party)
        db.session.commit()

        flash("Party added successfully.", "success")
        return redirect(url_for("parties"))

    return render_template(
        "add_party.html",
        party_types=PARTY_TYPES,
        form_data={},
        edit_mode=False,
    )


@app.route("/parties/<int:party_id>/edit", methods=["GET", "POST"])
@login_required
def edit_party(party_id):
    party = Party.query.filter_by(id=party_id, user_id=g.user.id).first_or_404()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        party_type = request.form.get("party_type", "other").strip().lower()
        notes = request.form.get("notes", "").strip()

        if not name:
            flash("Party name is required.", "danger")
            return render_template(
                "add_party.html",
                party_types=PARTY_TYPES,
                party=party,
                form_data=request.form,
                edit_mode=True,
            )

        if party_type not in PARTY_TYPES:
            flash("Invalid party type.", "danger")
            return render_template(
                "add_party.html",
                party_types=PARTY_TYPES,
                party=party,
                form_data=request.form,
                edit_mode=True,
            )

        party.name = name
        party.phone = phone
        party.party_type = party_type
        party.notes = notes

        db.session.commit()
        flash("Party updated successfully.", "success")
        return redirect(url_for("parties"))

    return render_template(
        "add_party.html",
        party_types=PARTY_TYPES,
        party=party,
        form_data=party,
        edit_mode=True,
    )


@app.route("/parties/<int:party_id>/delete", methods=["POST"])
@login_required
def delete_party(party_id):
    party = Party.query.filter_by(id=party_id, user_id=g.user.id).first_or_404()

    db.session.delete(party)
    db.session.commit()

    flash("Party deleted successfully.", "info")
    return redirect(url_for("parties"))


@app.route("/transactions")
@login_required
def transactions():
    transactions_list = (
        Transaction.query.filter_by(user_id=g.user.id)
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .all()
    )
    return render_template(
        "transactions.html",
        transactions=transactions_list,
        transaction_types=TRANSACTION_TYPES,
    )


@app.route("/transactions/add", methods=["GET", "POST"])
@login_required
def add_transaction():
    parties_list = Party.query.filter_by(user_id=g.user.id).order_by(Party.name.asc()).all()

    if request.method == "POST":
        party_id_raw = request.form.get("party_id", "").strip()
        transaction_type = request.form.get("transaction_type", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        description = request.form.get("description", "").strip()
        date_raw = request.form.get("date", "").strip()

        if transaction_type not in TRANSACTION_TYPES:
            flash("Invalid transaction type.", "danger")
            return render_template(
                "add_transaction.html",
                parties=parties_list,
                transaction_types=TRANSACTION_TYPES,
                form_data=request.form,
                edit_mode=False,
            )

        amount = parse_amount(amount_raw)
        if amount is None:
            flash("Amount must be a valid number greater than 0.", "danger")
            return render_template(
                "add_transaction.html",
                parties=parties_list,
                transaction_types=TRANSACTION_TYPES,
                form_data=request.form,
                edit_mode=False,
            )

        tx_date = parse_date(date_raw)
        if tx_date is None:
            flash("Please provide a valid date.", "danger")
            return render_template(
                "add_transaction.html",
                parties=parties_list,
                transaction_types=TRANSACTION_TYPES,
                form_data=request.form,
                edit_mode=False,
            )

        party = None
        if party_id_raw:
            if not party_id_raw.isdigit():
                flash("Invalid party selection.", "danger")
                return render_template(
                    "add_transaction.html",
                    parties=parties_list,
                    transaction_types=TRANSACTION_TYPES,
                    form_data=request.form,
                    edit_mode=False,
                )

            party = Party.query.filter_by(
                id=int(party_id_raw), user_id=g.user.id
            ).first()
            if not party:
                flash("Selected party does not exist.", "danger")
                return render_template(
                    "add_transaction.html",
                    parties=parties_list,
                    transaction_types=TRANSACTION_TYPES,
                    form_data=request.form,
                    edit_mode=False,
                )

        transaction = Transaction(
            user_id=g.user.id,
            party_id=party.id if party else None,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            date=tx_date,
        )
        db.session.add(transaction)
        db.session.commit()

        flash("Transaction added successfully.", "success")
        return redirect(url_for("transactions"))

    return render_template(
        "add_transaction.html",
        parties=parties_list,
        transaction_types=TRANSACTION_TYPES,
        form_data={"date": datetime.today().strftime("%Y-%m-%d")},
        edit_mode=False,
    )


@app.route("/transactions/<int:transaction_id>/edit", methods=["GET", "POST"])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.filter_by(
        id=transaction_id, user_id=g.user.id
    ).first_or_404()
    parties_list = Party.query.filter_by(user_id=g.user.id).order_by(Party.name.asc()).all()

    if request.method == "POST":
        party_id_raw = request.form.get("party_id", "").strip()
        transaction_type = request.form.get("transaction_type", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        description = request.form.get("description", "").strip()
        date_raw = request.form.get("date", "").strip()

        if transaction_type not in TRANSACTION_TYPES:
            flash("Invalid transaction type.", "danger")
            return render_template(
                "add_transaction.html",
                parties=parties_list,
                transaction_types=TRANSACTION_TYPES,
                transaction=transaction,
                form_data=request.form,
                edit_mode=True,
            )

        amount = parse_amount(amount_raw)
        if amount is None:
            flash("Amount must be a valid number greater than 0.", "danger")
            return render_template(
                "add_transaction.html",
                parties=parties_list,
                transaction_types=TRANSACTION_TYPES,
                transaction=transaction,
                form_data=request.form,
                edit_mode=True,
            )

        tx_date = parse_date(date_raw)
        if tx_date is None:
            flash("Please provide a valid date.", "danger")
            return render_template(
                "add_transaction.html",
                parties=parties_list,
                transaction_types=TRANSACTION_TYPES,
                transaction=transaction,
                form_data=request.form,
                edit_mode=True,
            )

        party = None
        if party_id_raw:
            if not party_id_raw.isdigit():
                flash("Invalid party selection.", "danger")
                return render_template(
                    "add_transaction.html",
                    parties=parties_list,
                    transaction_types=TRANSACTION_TYPES,
                    transaction=transaction,
                    form_data=request.form,
                    edit_mode=True,
                )

            party = Party.query.filter_by(
                id=int(party_id_raw), user_id=g.user.id
            ).first()
            if not party:
                flash("Selected party does not exist.", "danger")
                return render_template(
                    "add_transaction.html",
                    parties=parties_list,
                    transaction_types=TRANSACTION_TYPES,
                    transaction=transaction,
                    form_data=request.form,
                    edit_mode=True,
                )

        transaction.party_id = party.id if party else None
        transaction.transaction_type = transaction_type
        transaction.amount = amount
        transaction.description = description
        transaction.date = tx_date

        db.session.commit()
        flash("Transaction updated successfully.", "success")
        return redirect(url_for("transactions"))

    return render_template(
        "add_transaction.html",
        parties=parties_list,
        transaction_types=TRANSACTION_TYPES,
        transaction=transaction,
        form_data={
            "party_id": transaction.party_id,
            "transaction_type": transaction.transaction_type,
            "amount": transaction.amount,
            "description": transaction.description,
            "date": transaction.date.strftime("%Y-%m-%d"),
        },
        edit_mode=True,
    )


@app.route("/transactions/<int:transaction_id>/delete", methods=["POST"])
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.filter_by(
        id=transaction_id, user_id=g.user.id
    ).first_or_404()

    db.session.delete(transaction)
    db.session.commit()

    flash("Transaction deleted successfully.", "info")
    return redirect(url_for("transactions"))


@app.route("/ledger/<int:party_id>")
@login_required
def ledger(party_id):
    party = Party.query.filter_by(id=party_id, user_id=g.user.id).first_or_404()
    entries = (
        Transaction.query.filter_by(user_id=g.user.id, party_id=party.id)
        .order_by(Transaction.date.asc(), Transaction.created_at.asc())
        .all()
    )

    total_receivable, total_payable = calculate_receivable_payable(entries)
    net_balance = total_receivable - total_payable

    return render_template(
        "ledger.html",
        party=party,
        entries=entries,
        total_receivable=total_receivable,
        total_payable=total_payable,
        net_balance=net_balance,
        transaction_types=TRANSACTION_TYPES,
    )


if __name__ == "__main__":
    app.run(debug=True)
