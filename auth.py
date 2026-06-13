from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

from forms import LoginForm, RegisterForm
from database import get_connection

auth_bp = Blueprint("auth", __name__)


# REGISTER
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (form.email.data,))
        existing = cursor.fetchone()

        if existing:
            flash("Email already registered.", "danger")
            cursor.close()
            conn.close()
            return render_template("register.html", form=form)

        # Insert new user
        cursor.execute("""
            INSERT INTO users (email, password_hash)
            VALUES (%s, %s)
        """, (
            form.email.data,
            generate_password_hash(form.password.data)
        ))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login", email=form.email.data))

    return render_template("register.html", form=form)


# LOGIN
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    # Pre-fill email if passed as query param
    if request.method == "GET":
        email = request.args.get("email")
        if email:
            form.email.data = email

    if form.validate_on_submit(): 
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email = %s", (form.email.data,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user["password_hash"], form.password.data):
            access_token = create_access_token(identity=str(user["id"]))

            response = redirect(url_for("dashboard"))
            response.set_cookie("access_token", access_token, httponly=True)

            flash("Logged in successfully.", "success")
            return response

        flash("Invalid credentials.", "danger")

    return render_template("login.html", form=form)


# LOGOUT
@auth_bp.route("/logout")
def logout():
    response = redirect(url_for("auth.login"))
    response.delete_cookie("access_token")

    flash("Logged out successfully.", "success")
    return response
