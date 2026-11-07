import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import create_app  # noqa: E402


@pytest.fixture
def cli(tmp_path):
    app = create_app(str(tmp_path / "teste.db"))
    app.config["TESTING"] = True
    return app.test_client()


def cadastrar(c, email="ana@exemplo.com"):
    return c.post("/api/cadastro", json={"nome": "Ana", "email": email, "telefone": "87999999999", "senha": "123456"})


def amanha():
    return (date.today() + timedelta(days=1)).isoformat()


def test_cadastro_ok_e_email_duplicado(cli):
    assert cadastrar(cli).status_code == 201
    assert cadastrar(cli).status_code == 409


def test_cadastro_invalido(cli):
    r = cli.post("/api/cadastro", json={"nome": "", "email": "x", "senha": "1"})
    assert r.status_code == 400


def test_login_senha_errada(cli):
    cadastrar(cli)
    r = cli.post("/api/login", json={"email": "ana@exemplo.com", "senha": "errada"})
    assert r.status_code == 401


def test_agendar_exige_login(cli):
    r = cli.post("/api/agendamentos", json={"servico_id": 1, "data": amanha(), "hora": "09:00"})
    assert r.status_code == 401


def test_agendar_conflito_e_cancelar(cli):
    cadastrar(cli)
    corpo = {"servico_id": 1, "data": amanha(), "hora": "09:00"}
    r = cli.post("/api/agendamentos", json=corpo)
    assert r.status_code == 201
    assert cli.post("/api/agendamentos", json=corpo).status_code == 409
    assert cli.delete(f"/api/agendamentos/{r.get_json()['id']}").status_code == 200
    assert cli.post("/api/agendamentos", json=corpo).status_code == 201


def test_data_passada(cli):
    cadastrar(cli)
    ontem = (date.today() - timedelta(days=1)).isoformat()
    r = cli.post("/api/agendamentos", json={"servico_id": 1, "data": ontem, "hora": "09:00"})
    assert r.status_code == 400


def test_telefone_com_letras(cli):
    r = cli.post("/api/cadastro", json={"nome": "Ana", "email": "a@b.com", "telefone": "abc", "senha": "123456"})
    assert r.status_code == 400


def test_servicos_tem_preco(cli):
    assert all("preco" in s for s in cli.get("/api/servicos").get_json())


def test_remarcar(cli):
    cadastrar(cli)
    ag = cli.post("/api/agendamentos", json={"servico_id": 1, "data": amanha(), "hora": "09:00"}).get_json()["id"]
    assert cli.put(f"/api/agendamentos/{ag}", json={"data": amanha(), "hora": "10:00"}).status_code == 200
    assert cli.get("/api/agendamentos").get_json()[0]["hora"] == "10:00"
    ontem = (date.today() - timedelta(days=1)).isoformat()
    assert cli.put(f"/api/agendamentos/{ag}", json={"data": ontem, "hora": "10:00"}).status_code == 400


def test_horario_que_ja_passou_hoje(cli, monkeypatch):
    import app as appmod
    from datetime import datetime
    monkeypatch.setattr(appmod, "agora", lambda: datetime(2030, 1, 1, 15, 0, tzinfo=appmod.FUSO))
    cadastrar(cli)
    assert cli.post("/api/agendamentos", json={"servico_id": 1, "data": "2030-01-01", "hora": "09:00"}).status_code == 400
    assert cli.post("/api/agendamentos", json={"servico_id": 1, "data": "2030-01-01", "hora": "16:00"}).status_code == 201
