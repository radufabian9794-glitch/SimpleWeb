#!/usr/bin/env python
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "postgresql://user:pass@db:5432/mydb"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

with app.app_context():
    try:
        db.session.execute("""
            ALTER TABLE transactions
            ADD COLUMN merchant VARCHAR(255);
        """)
        db.session.commit()
        print("✓ Successfully added merchant column to transactions table")
    except Exception as e:
        db.session.rollback()
        if "already exists" in str(e):
            print("✓ merchant column already exists")
        else:
            print(f"✗ Error: {e}")
