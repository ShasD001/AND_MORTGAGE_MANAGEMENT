import os

class Config:
    # Flask security keys
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-key-change-me")

    # JWT cookie settings
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_ACCESS_COOKIE_NAME = "access_token"
    JWT_COOKIE_CSRF_PROTECT = False

    # MySQL database configuration
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "password")
    MYSQL_DB = os.environ.get("MYSQL_DB", "mortgage_app")

    # API Ninjas config
    API_NINJAS_BASE_URL = "https://api.api-ninjas.com"
    API_NINJAS_MORTGAGE_RATE_ENDPOINT = "/v2/mortgagerate"
    API_NINJAS_MORTGAGE_CALCULATOR_ENDPOINT = "/v1/mortgagecalculator"
    API_NINJAS_KEY = os.environ.get("API_NINJAS_KEY", "CHANGE_ME")
