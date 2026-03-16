import os
import logging
from database import init_db
from flask import Flask, jsonify, render_template, request

from interfaces.api.routes import register_api_routes
from interfaces.web.routes import register_web_routes
from infrastructure.container import prospeccao_repository

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Context processor para disponibilizar dados globais em todos os templates
@app.context_processor
def inject_globals():
    try:
        return {
            'total_retornos_hoje': prospeccao_repository().get_total_retornos_hoje()
        }
    except Exception as e:
        logger.error(f"Erro ao injetar globais: {e}")
        return {'total_retornos_hoje': 0}


# ==================== ERROR Handlers ====================

@app.errorhandler(400)
def bad_request(error):
    """Handler para erros 400 - Bad Request."""
    logger.warning(f"Bad Request: {error}")
    if request.path.startswith('/api/'):
        return jsonify({
            'ok': False,
            'message': 'Requisição inválida',
            'error': str(error)
        }), 400
    return render_template('error.html', 
        code=400, 
        message='Requisição inválida',
        active_page='error'
    ), 400


@app.errorhandler(404)
def not_found(error):
    """Handler para erros 404 - Not Found."""
    logger.warning(f"Not Found: {request.path}")
    if request.path.startswith('/api/'):
        return jsonify({
            'ok': False,
            'message': 'Recurso não encontrado'
        }), 404
    return render_template('error.html',
        code=404,
        message='Página não encontrada',
        active_page='error'
    ), 404


@app.errorhandler(500)
def internal_error(error):
    """Handler para erros 500 - Internal Server Error."""
    logger.error(f"Internal Server Error: {error}", exc_info=True)
    if request.path.startswith('/api/'):
        return jsonify({
            'ok': False,
            'message': 'Erro interno do servidor'
        }), 500
    return render_template('error.html',
        code=500,
        message='Erro interno do servidor',
        active_page='error'
    ), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handler global para exceções não tratadas."""
    logger.error(f"Unhandled Exception: {error}", exc_info=True)
    
    if request.path.startswith('/api/'):
        return jsonify({
            'ok': False,
            'message': 'Erro inesperado',
            'error': str(error) if app.debug else 'Erro interno'
        }), 500
    
    return render_template('error.html',
        code=500,
        message='Erro inesperado',
        active_page='error'
    ), 500


# Auto-init db se não existir
init_db()

register_web_routes(app)
register_api_routes(app)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
