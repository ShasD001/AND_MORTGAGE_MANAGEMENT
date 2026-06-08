from flask import Flask, render_template
from flask_jwt_extended import JWTManager
from config import Config
from auth import auth_bp
from database import init_db
from profile_routes import profile_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    JWTManager(app)

    # Initialise DB on startup
    init_db()

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/dashboard")
    def dashboard():
        # Protected page later
        return render_template("dashboard.html")

    return app

if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)