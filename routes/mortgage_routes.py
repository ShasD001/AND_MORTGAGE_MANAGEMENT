from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from forms import MortgageCalculatorForm

from database import (
    get_user_profile,
    get_latest_mortgage_summary,
    save_mortgage_result
)

from mortgage_calc import get_api_repayment_result
from services.mortgage_api_service import MortgageAPIError


mortgage_bp = Blueprint("mortgage", __name__)


@mortgage_bp.route("/mortgage-calculator", methods=["GET", "POST"])
@jwt_required()
def mortgage_calculator():
    # Gets the logged-in user's ID
    user_id = int(get_jwt_identity())

    # Checks if the user has completed their financial profile
    profile_data = get_user_profile(user_id)

    if profile_data is None:
        flash(
            "Please complete your financial profile before using the mortgage calculator.",
            "warning"
        )
        return redirect(url_for("profile.profile"))

    # Checks whether the user already has a mortgage calculation
    existing_result = get_latest_mortgage_summary(
        user_id=user_id,
        income_multiple=4.5
    )

    # If the user clicks Mortgage Calculator after already calculating,
    # send them back to the dashboard where the result is shown.
    if existing_result and request.method == "GET":
        flash(
            "You already have a mortgage calculation. Your latest result is shown on the dashboard.",
            "info"
        )
        return redirect(url_for("dashboard"))

    form = MortgageCalculatorForm()

    if form.validate_on_submit():
        amount = float(form.amount.data)
        rate = float(form.rate.data)
        term_years = int(form.term_years.data)

        try:
            api_values = get_api_repayment_result(
                amount=amount,
                rate=rate,
                term_years=term_years
            )

        except MortgageAPIError as error:
            flash(str(error), "danger")
            return render_template(
                "mortgage_calculator.html",
                form=form,
                profile_data=profile_data
            )

        save_mortgage_result(
            user_id=user_id,
            amount=amount,
            rate=rate,
            term_years=term_years,
            monthly_repayment=api_values["monthly_repayment"],
            annual_repayment=api_values["annual_repayment"],
            total_interest_payable=api_values["total_interest_payable"]
        )

        flash("Mortgage calculation completed successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template(
        "mortgage_calculator.html",
        form=form,
        profile_data=profile_data
    )