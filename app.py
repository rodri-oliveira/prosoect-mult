import os
from database import init_db
from flask import Flask

from interfaces.api.routes import register_api_routes
from interfaces.web.routes import register_web_routes
from infrastructure.container import prospeccao_repository
app = Flask(__name__)

# Context processor para disponibilizar dados globais em todos os templates
@app.context_processor
def inject_globals():
    return {
        'total_retornos_hoje': prospeccao_repository().get_total_retornos_hoje()
    }

# Auto-init db se não existir
init_db()

register_web_routes(app)
register_api_routes(app)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
