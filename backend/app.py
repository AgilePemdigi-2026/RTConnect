import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge
from config import Config
from database.db import query_one

# Import Route Blueprints
from routes.auth_routes import auth_bp
from routes.letter_routes import letter_bp
from routes.chatbot_routes import chatbot_bp
from routes.notification_routes import notification_bp

def create_app():
    Config.validate()
    app = Flask(__name__)
    app.config.from_object(Config)

    cors_origins = ["*"] if not Config.IS_PRODUCTION else Config.CORS_ORIGINS
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    if Config.STORAGE_BACKEND == 'local':
        for folder in [Config.UPLOAD_FOLDER, Config.SIGNATURES_FOLDER, Config.ATTACHMENTS_FOLDER, Config.LETTERS_FOLDER]:
            os.makedirs(folder, exist_ok=True)

    # Registrasi Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(letter_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(notification_bp)

    @app.route('/')
    def root():
        return jsonify({
            'success': True,
            'message': 'Selamat datang di RTConnect Backend REST API',
            'version': '1.0.0',
            'rt_community': Config.RT_AREA,
            'endpoints': {
                'auth': '/api/v1/auth',
                'letters': '/api/v1/letters',
                'chatbot': '/api/v1/chatbot',
                'notifications': '/api/v1/notifications',
                'health': '/api/v1/health'
            }
        }), 200

    @app.route('/api/v1/health', methods=['GET'])
    def health_check():
        db_status = 'ok'
        try:
            query_one("SELECT 1")
        except Exception:
            app.logger.exception('Database health check failed.')
            db_status = 'unavailable'

        return jsonify({
            'success': db_status == 'ok',
            'message': 'RTConnect API Server Status',
            'data': {
                'status': 'healthy' if db_status == 'ok' else 'degraded',
                'database': db_status,
                'rt_unit': Config.RT_AREA
            },
            'error': None if db_status == 'ok' else 'DATABASE_ERROR'
        }), 200 if db_status == 'ok' else 503

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({
            'success': False,
            'message': 'Endpoint atau sumber daya yang diminta tidak ditemukan',
            'data': None,
            'error': 'NOT_FOUND'
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return jsonify({
            'success': False,
            'message': 'Metode HTTP tidak diizinkan untuk endpoint ini',
            'data': None,
            'error': 'METHOD_NOT_ALLOWED'
        }), 405

    @app.errorhandler(500)
    def handle_server_error(e):
        app.logger.exception('Unhandled server error.', exc_info=e)
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan internal pada server',
            'data': None,
            'error': 'INTERNAL_SERVER_ERROR'
        }), 500

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_too_large(_e):
        return jsonify({
            'success': False,
            'message': 'Ukuran permintaan melebihi batas 10 MB',
            'data': None,
            'error': 'REQUEST_TOO_LARGE'
        }), 413

    return app

# Expose app instance untuk WSGI / Gunicorn (Railway, Render, dll)
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"[*] Menjalankan RTConnect Backend di http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=Config.APP_ENV == 'development')
