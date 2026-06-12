from flask import Blueprint, render_template, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import get_connection
from forms import ProfileForm


profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile", methods=["GET", "POST"])
@jwt_required()
def profile():
    user_id = int(get_jwt_identity())
    form = ProfileForm()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch existing profile
    cursor.execute(
        "SELECT * FROM user_profiles WHERE user_id = %s",
        (user_id,)
    )
    profile_data = cursor.fetchone()

    # Handle form submission
    if form.validate_on_submit():

        if profile_data:
            # UPDATE existing profile
            cursor.execute("""
                UPDATE user_profiles
                SET annual_income = %s,
                    credit_score = %s,
                    employment_type = %s,
                    monthly_expenses = %s,
                    monthly_debts = %s
                WHERE user_id = %s
            """, (
                form.annual_income.data,
                form.credit_score.data,
                form.employment_type.data,
                form.monthly_expenses.data,
                form.monthly_debts.data,
                user_id
            ))

        else:
            # INSERT new profile
            cursor.execute("""
                INSERT INTO user_profiles (
                    user_id,
                    annual_income,
                    credit_score,
                    employment_type,
                    monthly_expenses,
                    monthly_debts
                )
                VALUES (%s, %s, %s, %s, %s, %s)
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

    # Pre-fill form if profile exists
    if profile_data:
        form.annual_income.data = profile_data["annual_income"]
        form.credit_score.data = profile_data["credit_score"]
        form.employment_type.data = profile_data["employment_type"]
        form.monthly_expenses.data = profile_data["monthly_expenses"]
        form.monthly_debts.data = profile_data["monthly_debts"]

    conn.close()

    return render_template("profile.html", form=form)
