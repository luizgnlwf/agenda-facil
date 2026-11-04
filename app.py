"""Controller (MVC): rotas da API e validações. Execute com: python app.py"""
import re
import sqlite3
from datetime import date

from flask import Flask, g, jsonify, request, session

import models

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def create_app(db_path="agenda.db"):
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.secret_key = "troque-esta-chave"
    app.config["DB"] = db_path
    models.iniciar(db_path)

    def db():
        if "db" not in g:
            g.db = models.conectar(app.config["DB"])
        return g.db

    @app.teardown_appcontext
    def fechar(_):
        con = g.pop("db", None)
        if con:
            con.close()

    def erro(msg, codigo=400):
        return jsonify(erro=msg), codigo

    def data_valida(texto):
        try:
            d = date.fromisoformat(texto or "")
        except ValueError:
            return None, "Data inválida."
        if d < date.today():
            return None, "Não é possível agendar em data passada."
        return d, None

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.post("/api/cadastro")
    def cadastro():
        d = request.get_json(silent=True) or {}
        nome = (d.get("nome") or "").strip()
        email = (d.get("email") or "").strip().lower()
        senha = d.get("senha") or ""
        if not nome:
            return erro("Informe o nome.")
        if not EMAIL.match(email):
            return erro("E-mail inválido.")
        if len(senha) < 6:
            return erro("A senha deve ter ao menos 6 caracteres.")
        try:
            uid = models.criar_usuario(db(), nome, email, (d.get("telefone") or "").strip(), senha)
        except sqlite3.IntegrityError:
            return erro("E-mail já cadastrado.", 409)
        session["uid"] = uid
        return jsonify(id=uid, nome=nome), 201

    @app.post("/api/login")
    def login():
        d = request.get_json(silent=True) or {}
        u = models.autenticar(db(), (d.get("email") or "").strip().lower(), d.get("senha") or "")
        if not u:
            return erro("E-mail ou senha incorretos.", 401)
        session["uid"] = u["id"]
        return jsonify(id=u["id"], nome=u["nome"])

    @app.post("/api/logout")
    def logout():
        session.clear()
        return jsonify(ok=True)

    @app.get("/api/me")
    def me():
        u = models.buscar_usuario(db(), session.get("uid"))
        return jsonify(dict(u)) if u else erro("Não autenticado.", 401)

    @app.get("/api/servicos")
    def servicos():
        return jsonify(models.listar_servicos(db()))

    @app.get("/api/horarios")
    def horarios():
        d, msg = data_valida(request.args.get("data"))
        if msg:
            return erro(msg)
        ocupadas = models.horas_ocupadas(db(), d.isoformat())
        return jsonify([{"hora": h, "livre": h not in ocupadas} for h in models.HORARIOS])

    @app.post("/api/agendamentos")
    def agendar():
        uid = session.get("uid")
        if not uid:
            return erro("Faça login para agendar.", 401)
        d = request.get_json(silent=True) or {}
        dt, msg = data_valida(d.get("data"))
        if msg:
            return erro(msg)
        if d.get("hora") not in models.HORARIOS:
            return erro("Horário inválido.")
        if not models.servico_existe(db(), d.get("servico_id")):
            return erro("Serviço inválido.")
        try:
            ag = models.criar_agendamento(db(), uid, d["servico_id"], dt.isoformat(), d["hora"])
        except sqlite3.IntegrityError:
            return erro("Este horário já foi reservado.", 409)
        return jsonify(id=ag), 201

    @app.get("/api/agendamentos")
    def meus():
        uid = session.get("uid")
        if not uid:
            return erro("Faça login.", 401)
        return jsonify(models.listar_agendamentos(db(), uid))

    @app.delete("/api/agendamentos/<int:ag_id>")
    def cancelar(ag_id):
        uid = session.get("uid")
        if not uid:
            return erro("Faça login.", 401)
        if not models.cancelar_agendamento(db(), ag_id, uid):
            return erro("Agendamento não encontrado.", 404)
        return jsonify(ok=True)

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
