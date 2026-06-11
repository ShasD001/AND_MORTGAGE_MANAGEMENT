from flask import Blueprint, render_template, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity

from forms import MortgageCalculatorForm

from database import (
    get_user_profile,
    save_mortgage_result
)

from mortgage_calc import get_api_repayment_result
from services.mortgage_api_service import MortgageAPIError


mortgage_bp = Blueprint("mortgage", __name__)


@mortgage_bp.route("/mortgage-calculator", methods=["GET", "POST"])
@jwt_required()
def mortgage_calculator():
    user_id = int(get_jwt_identity())

    profile_data = get_user_profile(user_id)

    if profile_data is None:
        flash(
            "Please complete your financial profile before using the mortgage calculator.",
            "warning"
        )
        return redirect(url_for("profile.profile"))

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