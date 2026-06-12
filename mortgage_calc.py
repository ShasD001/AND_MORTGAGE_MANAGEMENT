from services.mortgage_api_service import (
    calculate_mortgage_payment,
    MortgageAPIError
)


def get_api_repayment_result(amount, rate, term_years):
    api_result = calculate_mortgage_payment(
        amount=amount,
        rate=rate,
        term_years=term_years
    )

    try:
        monthly_repayment = api_result["monthly_payment"]["total"]
        annual_repayment = api_result["annual_payment"]["total"]
        total_interest_payable = api_result["total_interest_paid"]

    except KeyError:
        raise MortgageAPIError(
            "The mortgage API returned an unexpected response format."
        )

    return {
        "monthly_repayment": round(monthly_repayment, 2),
        "annual_repayment": round(annual_repayment, 2),
        "total_interest_payable": round(total_interest_payable, 2)
    }