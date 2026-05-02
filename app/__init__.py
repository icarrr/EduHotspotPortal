from flask import Flask, render_template
from app.extensions import db, login_manager
from config import config


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)

    register_blueprints(app)
    register_error_handlers(app)

    return app


def register_blueprints(app):
    from app.routes.auth import bp as auth_bp
    from app.routes.main import bp as main_bp
    from app.routes.users import bp as users_bp
    from app.routes.settings import bp as settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(settings_bp)


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500


@login_manager.user_loader
def load_user(user_id):
    from app.models import Operator
    return Operator.query.get(int(user_id))
