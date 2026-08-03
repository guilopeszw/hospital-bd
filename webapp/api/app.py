import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_cors import CORS

from routes import analytics, analytics_orm, atendimentos, dashboard, escalas, faturamento, health, pacientes, profissionais, unidades, views

app = Flask(__name__)
CORS(app)

for blueprint in (
    dashboard.bp,
    pacientes.bp,
    profissionais.bp,
    atendimentos.bp,
    faturamento.bp,
    unidades.bp,
    escalas.bp,
    analytics.bp,
    analytics_orm.bp,
    views.bp,
    health.bp,
):
    app.register_blueprint(blueprint)

if __name__ == "__main__":
    # Porta 8000 (não 5000): no macOS o AirPlay/Control Center ocupa a
    # 5000 e responde 403, impedindo o front-end de alcançar a API.
    # Sobrescreva com a env PORT se precisar.
    app.run(debug=True, port=int(os.getenv("PORT", "5055")))
