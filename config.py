class Config:
    # Basic Flask config
    SECRET_KEY = "dev-secret-key-change-me"

    # JWT config for protected routes
    JWT_SECRET_KEY = "dev-jwt-secret-key-change-me"
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_ACCESS_COOKIE_NAME = "access_token"

    # Disable CSRF for this student project while using JWT cookies
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_CSRF_IN_COOKIES = False
    JWT_ACCESS_CSRF_HEADER_NAME = "X-CSRF-TOKEN"
    JWT_REFRESH_CSRF_HEADER_NAME = "X-CSRF-TOKEN"
    JWT_ACCESS_CSRF_FIELD_NAME = "csrf_token"
    JWT_REFRESH_CSRF_FIELD_NAME = "csrf_token"

    # SQLite database
    DATABASE = "mortgage_app.db"
    DATABASE_URI = "sqlite:///mortgage_app.db"

    # API Ninjas config
    API_NINJAS_BASE_URL = "https://api.api-ninjas.com"
    API_NINJAS_MORTGAGE_RATE_ENDPOINT = "/v2/mortgagerate"
    API_NINJAS_MORTGAGE_CALCULATOR_ENDPOINT = "/v1/mortgagecalculator"

    # Replace with your real API key later
    API_NINJAS_KEY = "a1bAaHfrR0fTt7bq7CMBXzxPc7r5f4imTF1Y2E8X"