"""Model (MVC): acesso ao banco SQLite e regras de dados."""
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

SERVICOS = [("Corte de cabelo", 30), ("Barba", 20), ("Corte + Barba", 50), ("Hidratação", 40)]
HORARIOS = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]


def conectar(path):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def iniciar(path):
    con = conectar(path)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE, telefone TEXT, senha TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS servicos(
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, duracao INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS agendamentos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
        servico_id INTEGER NOT NULL REFERENCES servicos(id),
        data TEXT NOT NULL, hora TEXT NOT NULL, UNIQUE(data, hora));
    """)
    if not con.execute("SELECT 1 FROM servicos").fetchone():
        con.executemany("INSERT INTO servicos(nome, duracao) VALUES(?, ?)", SERVICOS)
    con.commit()
    con.close()


def criar_usuario(con, nome, email, telefone, senha):
    cur = con.execute("INSERT INTO usuarios(nome, email, telefone, senha) VALUES(?,?,?,?)",
                      (nome, email, telefone, generate_password_hash(senha)))
    con.commit()
    return cur.lastrowid


def autenticar(con, email, senha):
    u = con.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    return u if u and check_password_hash(u["senha"], senha) else None


def buscar_usuario(con, uid):
    return con.execute("SELECT id, nome FROM usuarios WHERE id = ?", (uid,)).fetchone()


def listar_servicos(con):
    return [dict(r) for r in con.execute("SELECT id, nome, duracao FROM servicos")]


def servico_existe(con, sid):
    return con.execute("SELECT 1 FROM servicos WHERE id = ?", (sid,)).fetchone() is not None


def horas_ocupadas(con, data):
    return {r["hora"] for r in con.execute("SELECT hora FROM agendamentos WHERE data = ?", (data,))}


def criar_agendamento(con, uid, sid, data, hora):
    """Levanta sqlite3.IntegrityError se o horário já estiver ocupado."""
    cur = con.execute("INSERT INTO agendamentos(usuario_id, servico_id, data, hora) VALUES(?,?,?,?)",
                      (uid, sid, data, hora))
    con.commit()
    return cur.lastrowid


def listar_agendamentos(con, uid):
    rows = con.execute("""SELECT a.id, a.data, a.hora, s.nome AS servico FROM agendamentos a
                          JOIN servicos s ON s.id = a.servico_id
                          WHERE a.usuario_id = ? ORDER BY a.data, a.hora""", (uid,))
    return [dict(r) for r in rows]


def cancelar_agendamento(con, ag_id, uid):
    cur = con.execute("DELETE FROM agendamentos WHERE id = ? AND usuario_id = ?", (ag_id, uid))
    con.commit()
    return cur.rowcount > 0
