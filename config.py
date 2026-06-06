class Config:
    # Basic Flask config
    SECRET_KEY = "dev-secret-key-change-me"  # used by Flask for sessions & CSRF

    # Database
    DATABASE_URI = "sqlite:///mortgage_app.db"

    # External mortgage API config
    MORTGAGE_API_BASE_URL = "https://api.examplemortgage.com"
    MORTGAGE_API_JWT_TOKEN = "your-api-jwt-token-here"  # stored here, not in env
