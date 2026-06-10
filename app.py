from flask import Flask, render_template, request, redirect, url_for, flash
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity

from config import Config
from auth import auth_bp
from database import (
    init_db,
    get_latest_mortgage_summary,
    save_mortgage_result
)
from profile_routes import profile_bp
from mortgages_calc import get_api_repayment_result
from Services.mortgage_api_service import MortgageAPIError


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    JWTManager(app)

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

        #Gets the latest saved mortgage from the database
        #Includes SQL Calculations for borrowing, affordability, repayment percentage etc)
        latest_result = get_latest_mortgage_summary(
            user_id=user_id,
            income_multiple=4.5
        )

        print("DASHBOARD DATABASE RESULT:", latest_result)

        return render_template(
            "dashboard.html",
            latest_result=latest_result
        )

    #Function that runs when user submits the mortgage form
    @app.route("/test-mortgage", methods=["POST"])
    @jwt_required()
    def test_mortgage():
        user_id = int(get_jwt_identity()) 
        
        amount = float(request.form.get("amount"))
        rate = float(request.form.get("rate"))
        term_years = int(request.form.get("term_years"))

        print("FORM VALUES:", amount, rate, term_years)

        try:
            api_values = get_api_repayment_result(
                amount=amount,
                rate=rate,
                term_years=term_years
            )

            print("API VALUES:", api_values)

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

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)