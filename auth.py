from flask import Blueprint, render_template, redirect, url_for, flash, request
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

