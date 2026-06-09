from flask import Flask, render_template, redirect, url_for, flash
from flask_jwt_extended import JWTManager, jwt_required
from flask_jwt_extended.exceptions import NoAuthorizationError
from config import Config
from auth import auth_bp
from database import init_db
from profile_routes import profile_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    JWTManager(app)
    
    @app.errorhandler(NoAuthorizationError)
    def handle_missing_jwt(error):
        flash("Please register or log in before accessing your profile and mortgage features.", "warning")
        return redirect(url_for("auth.register"))

    # Initialise DB on startup
    init_db()

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/dashboard")
    @jwt_required()
    def dashboard():
        return render_template("dashboard.html")

    return app

if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)