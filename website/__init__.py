from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

db = SQLAlchemy()
DB_NAME = "database.db"



def create_app():
    app = Flask(__name__)
    bootstrap = Bootstrap(app)
    app.config["SECRET_KEY"] = "RAJ THE KELLYANTE KING"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_NAME}"
    db.init_app(app)

    # Register Roots/Blueprints
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    return app
