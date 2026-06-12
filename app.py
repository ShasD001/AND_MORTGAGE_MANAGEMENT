from flask import Flask, render_template, redirect, url_for, flash

from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    get_jwt_identity
)

from flask_jwt_extended.exceptions import NoAuthorizationError

from config import Config
from auth import auth_bp

from routes.profile_routes import profile_bp
from routes.mortgage_routes import mortgage_bp

from database import (
    init_db,
    get_connection,
    get_latest_mortgage_summary
)

from eligibility_checker import check_bank_eligibility


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

    # Initialize MySQL tables
    init_db()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(mortgage_bp)

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

    @app.route("/eligibility")
    @jwt_required()
    def eligibility():
        user_id = int(get_jwt_identity())

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch profile
        cursor.execute("""
            SELECT *
            FROM user_profiles
            WHERE user_id = %s
        """, (user_id,))

        profile = cursor.fetchone()

        if not profile:
            conn.close()
            flash(
                "Please complete your financial profile before checking bank eligibility.",
                "warning"
            )
            return redirect(url_for("profile.profile"))

        # Fetch latest mortgage
        cursor.execute("""
            SELECT *
            FROM mortgages
            WHERE user_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT 1
        """, (user_id,))

        mortgage = cursor.fetchone()

        if not mortgage:
            conn.close()
            flash(
                "Please complete a mortgage calculation before checking bank eligibility.",
                "warning"
            )
            return redirect(url_for("dashboard"))

        # Calculate LTV
        assumed_property_price = mortgage["amount"] / 0.85
        ltv = round((mortgage["amount"] / assumed_property_price) * 100, 2)

        mortgage_data = {
            "id": mortgage["id"],
            "amount": mortgage["amount"],
            "ltv": ltv
        }

        # Fetch active banks
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

            # Save eligibility result
            cursor.execute("""
                INSERT INTO eligibility_results (
                    mortgage_id,
                    bank_id,
                    eligible,
                    reason
                )
                VALUES (%s, %s, %s, %s)
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
