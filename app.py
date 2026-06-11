from flask import Flask, render_template, request, redirect, url_for, flash

from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_jwt_extended.exceptions import NoAuthorizationError

from config import Config
from auth import auth_bp
from profile_routes import profile_bp

from database import (
    init_db,
    get_connection,
    get_latest_mortgage_summary,
    save_mortgage_result
)

from eligibility_checker import check_bank_eligibility
from mortgage_calc import get_api_repayment_result
from services.mortgage_api_service import MortgageAPIError


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    JWTManager(app)

    @app.errorhandler(NoAuthorizationError)
    def handle_missing_jwt(error):
        flash(
            "Please register or log in before accessing your profile and mortgage features.",
            "warning"
        )
        return redirect(url_for("auth.register"))

    init_db()

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/dashboard")
    @jwt_required()
    def dashboard():
        user_id = int(get_jwt_identity())

        latest_result = get_latest_mortgage_summary(
            user_id=user_id,
            income_multiple=4.5
        )

        return render_template(
            "dashboard.html",
            latest_result=latest_result
        )

    @app.route("/test-mortgage", methods=["POST"])
    @jwt_required()
    def test_mortgage():
        user_id = int(get_jwt_identity())

        amount = float(request.form.get("amount"))
        rate = float(request.form.get("rate"))
        term_years = int(request.form.get("term_years"))

        try:
            api_values = get_api_repayment_result(
                amount=amount,
                rate=rate,
                term_years=term_years
            )

        except MortgageAPIError as error:
            flash(str(error), "danger")
            return redirect(url_for("dashboard"))

        save_mortgage_result(
            user_id=user_id,
            amount=amount,
            rate=rate,
            term_years=term_years,
            monthly_repayment=api_values["monthly_repayment"],
            annual_repayment=api_values["annual_repayment"],
            total_interest_payable=api_values["total_interest_payable"]
        )

        flash("Mortgage API calculation saved to the database.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/eligibility")
    @jwt_required()
    def eligibility():
        user_id = int(get_jwt_identity())

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM user_profiles
            WHERE user_id = ?
        """, (user_id,))
        profile = cursor.fetchone()

        if not profile:
            conn.close()
            flash("Please complete your financial profile before checking bank eligibility.", "warning")
            return redirect(url_for("profile.profile"))

        cursor.execute("""
            SELECT *
            FROM mortgages
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
        """, (user_id,))
        mortgage = cursor.fetchone()

        if not mortgage:
            conn.close()
            flash("Please complete a mortgage calculation before checking bank eligibility.", "warning")
            return redirect(url_for("dashboard"))

        # Temporary LTV assumption until property price/deposit are added.
        # Assumes the loan is 85% of the property value.
        assumed_property_price = mortgage["amount"] / 0.85
        ltv = round((mortgage["amount"] / assumed_property_price) * 100, 2)

        mortgage_data = {
            "id": mortgage["id"],
            "amount": mortgage["amount"],
            "ltv": ltv
        }

        cursor.execute("""
            SELECT *
            FROM banks
            WHERE active = 1
        """)
        banks = cursor.fetchall()

        results = []

        for bank in banks:
            eligible, reason = check_bank_eligibility(
                profile,
                mortgage_data,
                bank
            )

            cursor.execute("""
                INSERT INTO eligibility_results
                (mortgage_id, bank_id, eligible, reason)
                VALUES (?, ?, ?, ?)
            """, (
                mortgage["id"],
                bank["id"],
                1 if eligible else 0,
                reason
            ))

            results.append({
                "bank_name": bank["name"],
                "eligible": eligible,
                "reason": reason,
                "max_ltv": bank["max_ltv"],
                "max_income_multiple": bank["max_income_multiple"],
                "min_income": bank["min_income"],
                "accepted_employment_type": bank["accepted_employment_type"]
            })

        conn.commit()
        conn.close()

        return render_template(
            "eligibility_results.html",
            profile=profile,
            mortgage=mortgage,
            ltv=ltv,
            results=results
        )

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)