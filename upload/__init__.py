"""Aplication to manage Frostgrave wizards
"""
import os
import traceback
from flask import Flask, render_template, send_from_directory
from .ui import blueprint as ui_blueprint
from upload.database import db
from upload.admin import init_admin
from upload.template_filters import init_template_filters


def create_app(config):
    """ Used to create flask application"""
    app = Flask(__name__)
    app.config.from_object(config)

    with app.app_context():
        db.init_app(app)

    app.register_blueprint(ui_blueprint)
    init_admin(app)
    init_template_filters(app)

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
            'favicon.ico', mimetype='image/vnd.microsoft.icon')

    @app.errorhandler(404)
    def missing_page(exception):
        """Catch internal 404 errors, display
            a nice error page and log the error.
        """
        print(traceback.format_exc())
        return render_template('404.html'), 404

    @app.errorhandler(500)
    @app.errorhandler(Exception)
    def internal_error(exception):
        """Catch internal exceptions and 500 errors, display
            a nice error page and log the error.
        """
        print(traceback.format_exc())
        app.logger.error(traceback.format_exc())
        return render_template('500.html'), 500

    return app
