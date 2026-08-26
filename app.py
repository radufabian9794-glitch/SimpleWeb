import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash, check_password_hash
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "postgresql://user:pass@db:5432/mydb"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

site_title = "SimpleWeb" #for easy text replacement in templates
site_email_info = "info@simpleweb.com" #for easy text replacement in templates
site_email_support = "support@simpleweb.com" #for easy text replacement in templates
site_email_privacy = "privacy@simpleweb.com" #for easy text replacement in templates
site_url = "https://www.simpleweb.com" #for easy text replacement in templates
 
# ── Models ──────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"
 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    admin = db.Column(db.Integer, default=0, nullable=False)
 
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
 
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
 
    def __repr__(self):
        return f"<User {self.email}>"


class SiteSetting(db.Model):
    __tablename__ = "site_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)


# ── Routes ───────────────────────────────────────────────
def get_setting(key, default="0"):
    setting = SiteSetting.query.filter_by(key=key).first()
    return setting.value if setting else default


def set_setting(key, value):
    setting = SiteSetting.query.filter_by(key=key).first()
    if setting is None:
        setting = SiteSetting(key=key, value=str(value))
        db.session.add(setting)
    else:
        setting.value = str(value)
    db.session.commit()


def registration_enabled():
    return get_setting("registration_enabled", "1") == "1"


def login_enabled():
    return get_setting("login_enabled", "1") == "1"


def maintenance_enabled():
    return get_setting("maintenance_mode", "0") == "1"


@app.context_processor
def inject_user_context():
    return {
        "is_admin": bool(session.get("user_admin", 0)),
        "registration_enabled": registration_enabled(),
        "login_enabled": login_enabled(),
        "maintenance_enabled": maintenance_enabled(),
    }


@app.before_request
def enforce_maintenance():
    if not maintenance_enabled():
        return None

    if request.path.startswith("/static/"):
        return None

    if request.path in ["/maintenance", "/logout"]:
        return None

    if request.path == "/auth" and request.method == "GET":
        return None

    if request.path == "/login" and request.method == "POST":
        return None

    if bool(session.get("user_admin", 0)):
        return None

    return redirect(url_for("maintenance_page"))


@app.route("/")
def home():
    if "user_id" in session:
        #flash("You are already logged in.(code: 001)", "success")
        return render_template("index.html", title=site_title, name=session["user_name"])
    #flash("You are not logged in.", "error")
    return render_template("index.html", title=site_title)
 
 
@app.route("/auth")
def auth():
    if maintenance_enabled():
        flash("The site is currently under maintenance. Please try again later.", "error")
        return redirect(url_for("maintenance_page"))
    if "user_id" in session:
        flash("You are already logged in.(code: 002)", "success")
        return render_template("dashboard.html", name=session["user_name"] )
    return render_template(
        "auth.html",
        title=site_title,
        registration_enabled=registration_enabled(),
        login_enabled=login_enabled(),
    )
 
@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
 
    if not registration_enabled():
        flash("Registration is currently disabled.", "error")
        return redirect(url_for("auth") + "#register")

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
    session["user_admin"] = user.admin
 
    flash(f"Welcome, {user.name}! Your account has been created.", "success")
    return redirect(url_for("dashboard"))
 
 
@app.route("/login", methods=["POST"])
def login():
    
    
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
 
    if not login_enabled():
        flash("Login is currently disabled.", "error")
        return render_template(
            "auth.html",
            title=site_title,
            login_email=email,
            registration_enabled=registration_enabled(),
            login_enabled=login_enabled(),
        )

    user = User.query.filter_by(email=email).first()
 
    if not user or not user.check_password(password):
        flash("Invalid email or password.", "error")
        return render_template(
            "auth.html",
            title=site_title,
            login_email=email,
            registration_enabled=registration_enabled(),
            login_enabled=login_enabled(),
        )
 
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["user_admin"] = user.admin
 
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
    return render_template("dashboard.html", title=site_title, name=session["user_name"] )

@app.route("/admin", methods=["GET", "POST"])
def admin_page():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))

    user = User.query.get(session["user_id"])
    if not user or user.admin != 1:
        flash("You do not have permission to access the admin area.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        registration_enabled_value = request.form.get("registration_enabled") == "on"
        login_enabled_value = request.form.get("login_enabled") == "on"
        maintenance_enabled_value = request.form.get("maintenance_mode") == "on"
        set_setting("registration_enabled", int(registration_enabled_value))
        set_setting("login_enabled", int(login_enabled_value))
        set_setting("maintenance_mode", int(maintenance_enabled_value))
        flash("Security settings updated successfully.", "success")

    return render_template(
        "admin.html",
        title=site_title,
        name=user.name,
        registration_enabled=registration_enabled(),
        login_enabled=login_enabled(),
        maintenance_enabled=maintenance_enabled(),
    )


def _serialize_model_rows(model):
    rows = model.query.all()
    result = []
    for r in rows:
        row = {}
        for c in r.__table__.columns:
            val = getattr(r, c.name)
            # JSON serialize datetimes or other non-JSONable types if needed
            if isinstance(val, datetime):
                val = val.isoformat()
            row[c.name] = val
        result.append(row)
    return result

def _clear_table_and_dependents(table_name):
    inspector = inspect(db.engine)
    # First, delete rows from tables that reference this table via foreign keys
    for t in inspector.get_table_names():
        try:
            fks = inspector.get_foreign_keys(t)
        except Exception:
            fks = []
        for fk in fks:
            referred = fk.get("referred_table")
            if referred == table_name:
                db.session.execute(text(f"DELETE FROM {t}"))

    # Then delete from the requested table
    db.session.execute(text(f"DELETE FROM {table_name}"))
    # NOTE: do not commit here; caller should manage transaction scope to avoid nested transactions


def _clear_table_and_dependents_session(table_name, session):
    inspector = inspect(db.engine)
    for t in inspector.get_table_names():
        try:
            fks = inspector.get_foreign_keys(t)
        except Exception:
            fks = []
        for fk in fks:
            referred = fk.get("referred_table")
            if referred == table_name:
                session.execute(text(f"DELETE FROM {t}"))
    session.execute(text(f"DELETE FROM {table_name}"))


def _validate_foreign_keys_for_rows_session(table_name, rows, session):
    inspector = inspect(db.engine)
    fks = inspector.get_foreign_keys(table_name)
    for fk in fks:
        constrained = fk.get("constrained_columns") or fk.get("constrained_columns")
        referred_table = fk.get("referred_table")
        referred_cols = fk.get("referred_columns")
        if not constrained or not referred_table or not referred_cols:
            continue
        if len(constrained) != 1 or len(referred_cols) != 1:
            return False, f"Composite foreign key validation not supported for {table_name}."
        col = constrained[0]
        ref_col = referred_cols[0]

        vals = {r.get(col) for r in rows if r.get(col) is not None}
        if not vals:
            continue

        placeholders = []
        params = {}
        for i, v in enumerate(sorted(vals)):
            key = f"v{i}"
            placeholders.append(f":" + key)
            params[key] = v

        sql = text(f"SELECT DISTINCT {ref_col} FROM {referred_table} WHERE {ref_col} IN ({', '.join(placeholders)})")
        found = session.execute(sql, params).fetchall()
        found_set = {row[0] for row in found}
        missing = set(vals) - found_set
        if missing:
            return False, f"Missing references in {referred_table}.{ref_col}: {sorted(missing)}"

    return True, None


def _validate_foreign_keys_for_rows(table_name, rows):
    """Validate that values referenced by foreign keys in `rows` exist in their referenced tables.
    Returns (True, None) on success or (False, error_message) on failure.
    Supports single-column FKs only.
    """
    inspector = inspect(db.engine)
    fks = inspector.get_foreign_keys(table_name)
    for fk in fks:
        constrained = fk.get("constrained_columns") or fk.get("constrained_columns")
        referred_table = fk.get("referred_table")
        referred_cols = fk.get("referred_columns")
        if not constrained or not referred_table or not referred_cols:
            continue
        if len(constrained) != 1 or len(referred_cols) != 1:
            return False, f"Composite foreign key validation not supported for {table_name}."
        col = constrained[0]
        ref_col = referred_cols[0]

        vals = {r.get(col) for r in rows if r.get(col) is not None}
        if not vals:
            continue

        # build paramized IN clause
        placeholders = []
        params = {}
        for i, v in enumerate(sorted(vals)):
            key = f"v{i}"
            placeholders.append(f":" + key)
            params[key] = v

        sql = text(f"SELECT DISTINCT {ref_col} FROM {referred_table} WHERE {ref_col} IN ({', '.join(placeholders)})")
        found = db.session.execute(sql, params).fetchall()
        found_set = {row[0] for row in found}
        missing = set(vals) - found_set
        if missing:
            return False, f"Missing references in {referred_table}.{ref_col}: {sorted(missing)}"

    return True, None


@contextmanager
def transactional_session():
    """Context manager that begins a transaction, using a nested savepoint if one is already active."""
    # Some session wrappers (e.g., scoped_session proxy) may not expose `in_transaction`.
    try:
        active = db.session.in_transaction()
    except Exception:
        # Fallback: check generic `transaction` attribute
        active = getattr(db.session, "transaction", None) is not None

    if active:
        with db.session.begin_nested():
            yield
    else:
        with db.session.begin():
            yield


@app.route("/admin/backup/export")
def admin_backup_export():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))

    current_user = User.query.get(session["user_id"])
    if not current_user or current_user.admin != 1:
        flash("You do not have permission to access the admin area.", "error")
        return redirect(url_for("dashboard"))

    try:
        backup = {
            "users": _serialize_model_rows(User),
            "site_settings": _serialize_model_rows(SiteSetting),
            "transactions": _serialize_table_by_name("transactions") if inspect(db.engine).has_table("transactions") else [],
        }

        data = json.dumps(backup, indent=2)
        filename = f"simpleweb-backup-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
        flash("Backup export ready. Your download will start.", "success")
        return Response(
            data,
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment;filename={filename}"},
        )
    except Exception as e:
        flash(f"Failed to prepare backup: {e}", "error")
        return redirect(url_for("admin_page"))


@app.route("/admin/backup/export/users")
def admin_export_users():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))
    current_user = User.query.get(session["user_id"])
    if not current_user or current_user.admin != 1:
        flash("You do not have permission to access the admin area.", "error")
        return redirect(url_for("dashboard"))

    try:
        data = json.dumps(_serialize_model_rows(User), indent=2)
        filename = f"users-backup-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
        flash("Users export ready.", "success")
        return Response(data, mimetype="application/json", headers={"Content-Disposition": f"attachment;filename={filename}"})
    except Exception as e:
        flash(f"Failed to export users: {e}", "error")
        return redirect(url_for("admin_page"))


@app.route("/admin/backup/import/users", methods=["POST"])
def admin_import_users():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))
    current_user = User.query.get(session["user_id"])
    if not current_user or current_user.admin != 1:
        flash("You do not have permission to access the admin area.", "error")
        return redirect(url_for("dashboard"))

    f = request.files.get("backup_file")
    if not f:
        flash("No backup file uploaded.", "error")
        return redirect(url_for("admin_page"))

    try:
        payload = json.load(f)
    except Exception:
        flash("Uploaded file is not valid JSON.", "error")
        return redirect(url_for("admin_page"))

    try:
        rows = payload if isinstance(payload, list) else payload.get("users", [])
        SessionLocal = sessionmaker(bind=db.engine)
        db_sess = SessionLocal()
        try:
            with db_sess.begin():
                _clear_table_and_dependents_session("users", db_sess)
                for row in rows:
                    u = User()
                    for k, v in row.items():
                        setattr(u, k, v)
                    db_sess.add(u)
            flash("Users imported successfully.", "success")
        finally:
            db_sess.close()
    except Exception as e:
        flash(f"Failed to import users: {e}", "error")

    return redirect(url_for("admin_page"))


@app.route("/admin/backup/export/site_settings")
def admin_export_site_settings():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))
    current_user = User.query.get(session["user_id"])
    if not current_user or current_user.admin != 1:
        flash("You do not have permission to access the admin area.", "error")
        return redirect(url_for("dashboard"))

    try:
        data = json.dumps(_serialize_model_rows(SiteSetting), indent=2)
        filename = f"site-settings-backup-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
        flash("Site settings export ready.", "success")
        return Response(data, mimetype="application/json", headers={"Content-Disposition": f"attachment;filename={filename}"})
    except Exception as e:
        flash(f"Failed to export site settings: {e}", "error")
        return redirect(url_for("admin_page"))


@app.route("/admin/backup/import/site_settings", methods=["POST"])
def admin_import_site_settings():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))
    current_user = User.query.get(session["user_id"])
    if not current_user or current_user.admin != 1:
        flash("You do not have permission to access the admin area.", "error")
        return redirect(url_for("dashboard"))

    f = request.files.get("backup_file")
    if not f:
        flash("No backup file uploaded.", "error")
        return redirect(url_for("admin_page"))

    try:
        payload = json.load(f)
    except Exception:
        flash("Uploaded file is not valid JSON.", "error")
        return redirect(url_for("admin_page"))

    try:
        rows = payload if isinstance(payload, list) else payload.get("site_settings", [])
        SessionLocal = sessionmaker(bind=db.engine)
        db_sess = SessionLocal()
        try:
            with db_sess.begin():
                _clear_table_and_dependents_session("site_settings", db_sess)
                for row in rows:
                    s = SiteSetting()
                    for k, v in row.items():
                        setattr(s, k, v)
                    db_sess.add(s)
            flash("Site settings imported successfully.", "success")
        finally:
            db_sess.close()
    except Exception as e:
        flash(f"Failed to import site settings: {e}", "error")

    return redirect(url_for("admin_page"))


@app.route("/admin/backup/export/transactions")
def admin_export_transactions():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))
    current_user = User.query.get(session["user_id"])
    if not current_user or current_user.admin != 1:
        flash("You do not have permission to access the admin area.", "error")
        return redirect(url_for("dashboard"))

    try:
        if not inspect(db.engine).has_table("transactions"):
            flash("No transactions table present.", "error")
            return redirect(url_for("admin_page"))
        data = json.dumps(_serialize_table_by_name("transactions"), indent=2)
        filename = f"transactions-backup-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
        flash("Transactions export ready.", "success")
        return Response(data, mimetype="application/json", headers={"Content-Disposition": f"attachment;filename={filename}"})
    except Exception as e:
        flash(f"Failed to export transactions: {e}", "error")
        return redirect(url_for("admin_page"))


@app.route("/admin/backup/import/transactions", methods=["POST"])
def admin_import_transactions():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))
    current_user = User.query.get(session["user_id"])
    if not current_user or current_user.admin != 1:
        flash("You do not have permission to access the admin area.", "error")
        return redirect(url_for("dashboard"))

    if not inspect(db.engine).has_table("transactions"):
        flash("No transactions table present.", "error")
        return redirect(url_for("admin_page"))

    f = request.files.get("backup_file")
    if not f:
        flash("No backup file uploaded.", "error")
        return redirect(url_for("admin_page"))

    try:
        payload = json.load(f)
    except Exception:
        flash("Uploaded file is not valid JSON.", "error")
        return redirect(url_for("admin_page"))

    try:
        rows = payload if isinstance(payload, list) else payload.get("transactions", [])

        # Validate foreign keys first (e.g., user_id references users.id)
        ok, msg = _validate_foreign_keys_for_rows("transactions", rows)
        if not ok:
            flash(f"Failed to import transactions: {msg}", "error")
            return redirect(url_for("admin_page"))

        with transactional_session():
            _clear_table_and_dependents("transactions")
            inspector = inspect(db.engine)
            cols = [c["name"] for c in inspector.get_columns("transactions")]
            for row in rows:
                params = {c: row.get(c) for c in cols}
                cols_list = ",".join(cols)
                vals_list = ",".join([f":{c}" for c in cols])
                sql = text(f"INSERT INTO transactions ({cols_list}) VALUES ({vals_list})")
                db.session.execute(sql, params)

        flash("Transactions imported successfully.", "success")
    except Exception as e:
        flash(f"Failed to import transactions: {e}", "error")

    return redirect(url_for("admin_page"))


@app.route("/admin/backup/import", methods=["POST"])
def admin_backup_import():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))

    current_user = User.query.get(session["user_id"])
    if not current_user or current_user.admin != 1:
        flash("You do not have permission to access the admin area.", "error")
        return redirect(url_for("dashboard"))

    f = request.files.get("backup_file")
    if not f:
        flash("No backup file uploaded.", "error")
        return redirect(url_for("admin_page"))

    try:
        payload = json.load(f)
    except Exception:
        flash("Uploaded file is not valid JSON.", "error")
        return redirect(url_for("admin_page"))

    try:
        # If the uploaded JSON is the full backup object (users/site_settings/transactions), accept that
        if isinstance(payload, dict) and ("users" in payload or "site_settings" in payload or "transactions" in payload):
            users = payload.get("users", [])
            settings = payload.get("site_settings", [])
            transactions = payload.get("transactions", [])

            # Clear dependent tables then parents
            # perform imports inside one transaction and validate foreign keys
            SessionLocal = sessionmaker(bind=db.engine)
            db_sess = SessionLocal()
            try:
                with db_sess.begin():
                    # clear dependent tables first
                    _clear_table_and_dependents_session("transactions", db_sess)
                    _clear_table_and_dependents_session("users", db_sess)
                    _clear_table_and_dependents_session("site_settings", db_sess)

                    for row in users:
                        u = User()
                        for k, v in row.items():
                            setattr(u, k, v)
                        db_sess.add(u)

                    for row in settings:
                        s = SiteSetting()
                        for k, v in row.items():
                            setattr(s, k, v)
                        db_sess.add(s)

                    # flush so newly added parents are visible for FK validation
                    db_sess.flush()

                    # validate transactions referential integrity
                    if transactions:
                        ok, msg = _validate_foreign_keys_for_rows_session("transactions", transactions, db_sess)
                        if not ok:
                            raise Exception(msg)

                        inspector = inspect(db.engine)
                        cols = [c["name"] for c in inspector.get_columns("transactions")]
                        for row in transactions:
                            params = {c: row.get(c) for c in cols}
                            cols_list = ",".join(cols)
                            vals_list = ",".join([f":{c}" for c in cols])
                            sql = text(f"INSERT INTO transactions ({cols_list}) VALUES ({vals_list})")
                            db_sess.execute(sql, params)

                flash("Backup imported successfully.", "success")
            finally:
                db_sess.close()
        else:
            flash("Uploaded JSON did not contain recognized backup keys.", "error")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to import backup: {e}", "error")

    return redirect(url_for("admin_page"))


@app.route("/admin/users")
def admin_user_management():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))

    current_user = User.query.get(session["user_id"])
    if not current_user or current_user.admin != 1:
        flash("You do not have permission to access the admin area.", "error")
        return redirect(url_for("dashboard"))

    users = User.query.order_by(User.id).all()
    return render_template(
        "admin_users.html",
        title=site_title,
        name=current_user.name,
        users=users,
    )


@app.route("/admin/users/<int:user_id>/change-password", methods=["GET", "POST"])
def admin_user_change_password(user_id):
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))

    current_user = User.query.get(session["user_id"])
    if not current_user or current_user.admin != 1:
        flash("You do not have permission to access the admin area.", "error")
        return redirect(url_for("dashboard"))

    target_user = User.query.get(user_id)
    if not target_user:
        flash("User not found.", "error")
        return redirect(url_for("admin_user_management"))

    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return render_template(
                "admin_change_password.html",
                title=site_title,
                name=current_user.name,
                target_user=target_user,
            )

        if len(new_password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template(
                "admin_change_password.html",
                title=site_title,
                name=current_user.name,
                target_user=target_user,
            )

        target_user.set_password(new_password)
        db.session.commit()
        flash(f"Password for {target_user.name} updated successfully.", "success")
        return redirect(url_for("admin_user_management"))

    return render_template(
        "admin_change_password.html",
        title=site_title,
        name=current_user.name,
        target_user=target_user,
    )


@app.route("/maintenance")
def maintenance_page():
    if not maintenance_enabled():
        flash("Maintenance mode is not enabled.", "error")
        return redirect(url_for("home"))
    return render_template("maintenance.html", title=site_title)


@app.route("/profile")
def profile():
    if "user_id" not in session:
        flash("Please sign in to continue.", "error")
        return redirect(url_for("auth"))
    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("auth"))
    return render_template("profile.html", title=site_title, name=user.name, email=user.email )

@app.route("/profile/change-password", methods=["POST"])
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
 
@app.route('/privacy')
def privacy():
    if "user_id" in session:
        #flash("You are already logged in.(code: 001)", "success")
        return render_template("privacy.html", title=site_title, site_email_privacy=site_email_privacy, name=session["user_name"] )
    return render_template('privacy.html', title=site_title , site_email_privacy=site_email_privacy)

@app.route('/terms')
def terms():
    if "user_id" in session:
        return render_template('terms.html', title=site_title , site_email_info=site_email_info, name=session["user_name"] )
    return render_template('terms.html', title=site_title , site_email_info=site_email_info)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Handle form submission here
        pass
    
    if "user_id" in session:
        return render_template('contact.html', title=site_title , site_email_info=site_email_info, name=session["user_name"] )
    return render_template('contact.html', title=site_title , site_email_info=site_email_info)
# ── DB init ──────────────────────────────────────────────
def ensure_admin_column():
    inspector = inspect(db.engine)
    if not inspector.has_table("users"):
        db.create_all()
        return

    columns = {column["name"] for column in inspector.get_columns("users")}
    if "admin" not in columns:
        db.session.execute(text("ALTER TABLE users ADD COLUMN admin INTEGER NOT NULL DEFAULT 0"))
        db.session.commit()


def ensure_site_settings():
    if not inspect(db.engine).has_table("site_settings"):
        db.create_all()
        return

    for key, default in (("registration_enabled", "1"), ("login_enabled", "1"), ("maintenance_mode", "0")):
        if not SiteSetting.query.filter_by(key=key).first():
            db.session.add(SiteSetting(key=key, value=default))
    db.session.commit()

with app.app_context():
    db.create_all()
    ensure_admin_column()
    ensure_site_settings()
 
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
