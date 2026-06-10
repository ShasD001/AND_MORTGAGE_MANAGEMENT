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
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM user_profiles WHERE user_id = ?",
        (user_id,)
    )
    profile_data = cursor.fetchone()

    #Fetched profile data to be used for calculations and inserted into the table
    if form.validate_on_submit():
        annual_income = float(form.annual_income.data)
        credit_score = int(form.credit_score.data)
        employment_type = form.employment_type.data
        monthly_expenses = float(form.monthly_expenses.data)
        monthly_debts = float(form.monthly_debts.data)

        if profile_data:
            cursor.execute("""
                UPDATE user_profiles
                SET annual_income = ?,
                    credit_score = ?,
                    employment_type = ?,
                    monthly_expenses = ?,
                    monthly_debts = ?
                WHERE user_id = ?
            """, (
                annual_income,
                credit_score,
                employment_type,
                monthly_expenses,
                monthly_debts,
                user_id
            ))

        else:
            cursor.execute("""
                INSERT INTO user_profiles (
                    user_id,
                    annual_income,
                    credit_score,
                    employment_type,
                    monthly_expenses,
                    monthly_debts
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                annual_income,
                credit_score,
                employment_type,
                monthly_expenses,
                monthly_debts
            ))

        conn.commit()
        conn.close()

        flash("Profile saved successfully. You can now calculate your mortgage.", "success")
        return redirect(url_for("dashboard"))

    if profile_data:
        form.annual_income.data = profile_data["annual_income"]
        form.credit_score.data = profile_data["credit_score"]
        form.employment_type.data = profile_data["employment_type"]
        form.monthly_expenses.data = profile_data["monthly_expenses"]
        form.monthly_debts.data = profile_data["monthly_debts"]

    conn.close()
    return render_template("profile.html", form=form)