#Service to use the API
import requests
from config import Config


class MortgageAPIError(Exception):
    pass


def calculate_mortgage_payment(amount, rate, term_years):
    url = (
        Config.API_NINJAS_BASE_URL
        + Config.API_NINJAS_MORTGAGE_CALCULATOR_ENDPOINT
    )

    headers = {
        "X-Api-Key": Config.API_NINJAS_KEY,
        "Accept": "application/json"
    }

    params = {
        "loan_amount": amount,
        "interest_rate": rate,
        "duration_years": term_years
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            raise MortgageAPIError(
                f"Mortgage API failed: {response.status_code} - {response.text}"
            )

        return response.json()

    except requests.exceptions.RequestException as error:
        raise MortgageAPIError(
            f"Could not connect to mortgage API: {error}"
        )