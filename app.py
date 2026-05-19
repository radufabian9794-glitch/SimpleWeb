import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
 
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "postgresql://user:pass@db:5432/mydb"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
 
db = SQLAlchemy(app)
 
 
# ── Models ──────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"
 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
 
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
 
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
 
    def __repr__(self):
        return f"<User {self.email}>"


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)  # 'income' or 'expense'
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    merchant = db.Column(db.String(255), nullable=True)

    user = db.relationship("User", backref="transactions")

    def __repr__(self):
        return f"<Transaction {self.transaction_type} {self.amount}>"


# ── Routes ───────────────────────────────────────────────
@app.route("/")
def home():
    if "user_id" in session:
        #flash("You are already logged in.(code: 001)", "success")
        return render_template("index.html", title="Acme — Build things fast", name=session["user_name"])
    #flash("You are not logged in.", "error")
    return render_template("index.html", title="Acme — Build things fast")
 
 
@app.route("/auth")
def auth():
    if "user_id" in session:
        flash("You are already logged in.(code: 002)", "success")
        return render_template("dashboard.html", name=session["user_name"])
    flash("You are not logged in(code: 001).", "error")
    return render_template("auth.html")
 
 
@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
 
    if not name or not email or not password or not confirm_password:
        flash("All fields are required.", "error")
        return redirect(url_for("auth") + "#register")
 
    if password != confirm_password:
        flash("Passwords do not match.", "error")
        return redirect(url_for("auth") + "#register")
 
    if len(password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for("auth") + "#register")
 
    if User.query.filter_by(email=email).first():
        flash("An account with that email already exists.", "error")
        return redirect(url_for("auth") + "#register")
 
    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
 
    session["user_id"] = user.id
    session["user_name"] = user.name
 
    flash(f"Welcome, {user.name}! Your account has been created.", "success")
    return redirect(url_for("dashboard"))
 
 
@app.route("/login", methods=["POST"])
def login():
    
    
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
 
    user = User.query.filter_by(email=email).first()
 
    if not user or not user.check_password(password):
        flash("Invalid email or password.", "error")
        return redirect(url_for("auth"))
 
    session["user_id"] = user.id
    session["user_name"] = user.name
 
    flash(f"Welcome back, {user.name}!", "success")
    return redirect(url_for("dashboard"))
 
 
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))
 
 
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))
    return render_template("dashboard.html", name=session["user_name"])


@app.route("/profile")
def profile():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))
    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("auth"))
    return render_template("profile.html", name=user.name, email=user.email)

@app.route("/profile2")
def profile2():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))
    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("auth"))
    return render_template("profile2.html", name=user.name, email=user.email)

@app.route("/overview")
def overview():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))

    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("auth"))

    transactions = Transaction.query.filter_by(user_id=session["user_id"]).all()

    total_income = sum(t.amount for t in transactions if t.transaction_type == "income")
    total_spend = sum(t.amount for t in transactions if t.transaction_type == "expense")
    remaining = total_income - total_spend

    return render_template("overview.html", name=user.name,
                         total_income=total_income,
                         total_spend=total_spend,
                         remaining=remaining,
                         transactions=transactions)

@app.route("/transactions/add", methods=["POST"])
def add_transaction():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))

    amount = request.form.get("amount", "")
    transaction_type = request.form.get("type", "")
    date_str = request.form.get("date", "")
    description = request.form.get("description", "").strip()
    merchant = request.form.get("merchant", "").strip()

    if not amount or not transaction_type or not date_str:
        flash("Amount, type, and date are required.", "error")
        return redirect(url_for("overview"))

    try:
        amount = float(amount)
        if amount <= 0:
            flash("Amount must be greater than 0.", "error")
            return redirect(url_for("overview"))
    except ValueError:
        flash("Invalid amount.", "error")
        return redirect(url_for("overview"))

    if transaction_type not in ["income", "expense"]:
        flash("Invalid transaction type.", "error")
        return redirect(url_for("overview"))

    try:
        from datetime import datetime
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid date format.", "error")
        return redirect(url_for("overview"))

    transaction = Transaction(
        user_id=session["user_id"],
        amount=amount,
        transaction_type=transaction_type,
        date=date_obj,
        description=description if description else None,
        merchant=merchant if merchant else None
    )

    db.session.add(transaction)
    db.session.commit()

    flash("Transaction added successfully.", "success")
    return redirect(url_for("overview"))


@app.route("/transactions/<int:transaction_id>/edit", methods=["GET", "POST"])
def edit_transaction(transaction_id):
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))

    transaction = Transaction.query.get(transaction_id)
    if not transaction or transaction.user_id != session["user_id"]:
        flash("Transaction not found.", "error")
        return redirect(url_for("overview"))

    if request.method == "POST":
        amount = request.form.get("amount", "")
        transaction_type = request.form.get("type", "")
        date_str = request.form.get("date", "")
        description = request.form.get("description", "").strip()
        merchant = request.form.get("merchant", "").strip()

        if not amount or not transaction_type or not date_str:
            flash("Amount, type, and date are required.", "error")
            return redirect(url_for("edit_transaction", transaction_id=transaction_id))

        try:
            amount = float(amount)
            if amount <= 0:
                flash("Amount must be greater than 0.", "error")
                return redirect(url_for("edit_transaction", transaction_id=transaction_id))
        except ValueError:
            flash("Invalid amount.", "error")
            return redirect(url_for("edit_transaction", transaction_id=transaction_id))

        if transaction_type not in ["income", "expense"]:
            flash("Invalid transaction type.", "error")
            return redirect(url_for("edit_transaction", transaction_id=transaction_id))

        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format.", "error")
            return redirect(url_for("edit_transaction", transaction_id=transaction_id))

        transaction.amount = amount
        transaction.transaction_type = transaction_type
        transaction.date = date_obj
        transaction.description = description if description else None
        transaction.merchant = merchant if merchant else None
        db.session.commit()

        flash("Transaction updated successfully.", "success")
        return redirect(url_for("overview"))

    return render_template("edit_transaction.html", transaction=transaction, name=session["user_name"])


def change_password():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))

    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("auth"))

    if not user.check_password(current_password):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("profile"))

    if new_password != confirm_password:
        flash("New passwords do not match.", "error")
        return redirect(url_for("profile"))

    if len(new_password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for("profile"))

    user.set_password(new_password)
    db.session.commit()

    flash("Password updated successfully.", "success")
    return redirect(url_for("profile"))
 
 
# ── DB init ──────────────────────────────────────────────
with app.app_context():
    db.create_all()
 
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
