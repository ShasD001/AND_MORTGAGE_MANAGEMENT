from flask import Blueprint, render_template, redirect, url_for, flash
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm
from database import get_connection

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        conn = get_connection()
        cursor = conn.cursor()

        # Hash password before storing
        password_hash = generate_password_hash(form.password.data)

        try:
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (form.email.data, password_hash)
            )
            conn.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("auth.login"))
        except Exception:
            flash("Email already registered.", "danger")
        finally:
            conn.close()

    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (form.email.data,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], form.password.data):
            access_token = create_access_token(identity=str(user["id"]))

            response = redirect(url_for("dashboard"))
            response.set_cookie("access_token", access_token, httponly=True)

            flash("Logged in successfully.", "success")
            return response

    return render_template("login.html", form=form)

@auth_bp.route("/logout")
def logout():
    response = redirect(url_for("auth.login"))
    response.delete_cookie("access_token")
    flash("Logged out successfully.", "success")
    return response

