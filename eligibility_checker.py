def calculate_ltv(loan_amount, property_price):
    return round((loan_amount / property_price) * 100, 2)


def check_bank_eligibility(profile, mortgage, bank):
    reasons = []
    eligible = True

    annual_income = profile["annual_income"]
    employment_type = profile["employment_type"]
    loan_amount = mortgage["amount"]
    ltv = mortgage["ltv"]

    max_allowed_loan = annual_income * bank["max_income_multiple"]

    if annual_income < bank["min_income"]:
        eligible = False
        reasons.append("Income below minimum requirement.")

    if loan_amount > max_allowed_loan:
        eligible = False
        reasons.append("Requested loan exceeds this bank's income multiple.")

    if ltv > bank["max_ltv"]:
        eligible = False
        reasons.append(
            f"LTV is {ltv}%, but this bank only allows up to {bank['max_ltv']}%."
        )

    if employment_type != bank["accepted_employment_type"]:
        eligible = False
        reasons.append("Employment type not accepted by this bank.")

    if eligible:
        reasons.append("Eligible based on this bank's lending criteria.")

    return eligible, " ".join(reasons)