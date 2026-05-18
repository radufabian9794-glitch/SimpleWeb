from flask import Flask, jsonify, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html",
        title="My App",
        name="World",
        items=["Apples", "Bananas", "Cherries"]
    )

@app.route("/about")
def about():
    return "About page"

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
