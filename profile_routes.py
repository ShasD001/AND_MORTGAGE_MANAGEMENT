from flask import Blueprint, render_template, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_connection
from forms import ProfileForm

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile", methods=["GET", "POST"])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    form = ProfileForm()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
    profile_data = cursor.fetchone()

    if form.validate_on_submit():
        if profile_data:
            cursor.execute("""
                UPDATE user_profiles
                SET annual_income = ?, credit_score = ?, employment_type = ?,
                    monthly_expenses = ?, monthly_debts = ?
                WHERE user_id = ?
            """, (
                form.annual_income.data,
                form.credit_score.data,
                form.employment_type.data,
                form.monthly_expenses.data,
                form.monthly_debts.data,
                user_id
            ))
        else:
            cursor.execute("""
                INSERT INTO user_profiles
                (user_id, annual_income, credit_score, employment_type, monthly_expenses, monthly_debts)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                form.annual_income.data,
                form.credit_score.data,
                form.employment_type.data,
                form.monthly_expenses.data,
                form.monthly_debts.data
            ))

        conn.commit()
        conn.close()
        flash("Profile saved successfully.", "success")
        return redirect(url_for("dashboard"))

    if profile_data:
        form.annual_income.data = profile_data["annual_income"]
        form.credit_score.data = profile_data["credit_score"]
        form.employment_type.data = profile_data["employment_type"]
        form.monthly_expenses.data = profile_data["monthly_expenses"]
        form.monthly_debts.data = profile_data["monthly_debts"]

    conn.close()
    return render_template("profile.html", form=form)