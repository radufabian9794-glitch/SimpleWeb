import os
from flask import Flask, jsonify, render_template

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)

@app.route("/")
def home():
    return render_template("index.html", title="Acme — Build things fast")
 
@app.route("/auth")
def auth():
    return render_template("auth.html")
 
# Placeholder routes for the form submissions
@app.route("/login", methods=["POST"])
def login():
    # TODO: handle login logic
    return "Login submitted"
 
@app.route("/register", methods=["POST"])
def register():
    # TODO: handle registration logic
    return "Registration submitted"


@app.route("/api/users")
def users():
    return jsonify([
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ])

@app.route("/api/users/<int:user_id>")
def user(user_id):
    return jsonify({"id": user_id, "name": "Alice"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
