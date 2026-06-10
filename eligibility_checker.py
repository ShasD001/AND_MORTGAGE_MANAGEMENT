def check_bank_eligibility(profile, application, bank):

    reasons = []

    eligible = True

    annual_income = profile["annual_income"]
    employment_type = profile["employment_type"]

    loan_amount = application["loan_amount"]
    ltv = application["ltv"]

    max_allowed_loan = annual_income * bank["max_income_multiple"]

    if annual_income < bank["min_income"]:
        eligible = False
        reasons.append(
            "Income below minimum requirement."
        )

    if loan_amount > max_allowed_loan:
        eligible = False
        reasons.append(
            "Requested loan exceeds this bank's income multiple."
        )

    if ltv > bank["max_ltv"]:
        eligible = False
        reasons.append(
            f"LTV is {ltv}% but bank allows only {bank['max_ltv']}%."
        )

    if employment_type != bank["accepted_employment_type"]:
        eligible = False
        reasons.append(
            "Employment type not accepted."
        )

    if eligible:
        reasons.append(
            "Eligible based on lending criteria."
        )

    return eligible, reasons