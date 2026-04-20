import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


@pytest.fixture(scope="session")
def app_module():
    # Importa app com psycopg2 e smtplib mockados.
    with patch("psycopg2.connect"), patch("smtplib.SMTP"):
        import importlib
        import app as _app
        importlib.reload(_app)
        return _app


@pytest.fixture
def client(app_module):
    app_module.app.config["TESTING"] = True
    app_module.app.config["SECRET_KEY"] = "test-secret"
    with app_module.app.test_client() as c:
        yield c


@pytest.fixture
def logged_client(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Test User"
    return client


def make_receita(id=1, nome="Bolo de Chocolate", descricao="Bolo fofinho",
                 custo=25.50, tipo="doce", data="2024-01-15T10:00:00"):
    return {
        "id": id, "nome": nome, "descricao": descricao,
        "custo": custo, "tipo_receita": tipo, "data_registro": data,
    }


def _mock_row(data: dict):
    """Cria um MagicMock que imita DictRow do psycopg2."""
    row = MagicMock()
    row.keys.return_value = list(data.keys())
    row.__getitem__ = lambda self, k: data[k]
    row.__iter__ = lambda self: iter(data)
    return row


class TestAuth:

    # 1 - login com credenciais corretas
    def test_login_success(self, client, app_module):
        user_data = {"id": 1, "nome": "Admin", "login": "admin", "senha": "admin123", "situacao": "ativo"}
        with patch.object(app_module, "get_db") as mock_db:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchone.return_value = _mock_row(user_data)
            conn.cursor.return_value = cur
            mock_db.return_value = conn

            resp = client.post("/api/login",
                               data=json.dumps({"login": "admin", "senha": "admin123"}),
                               content_type="application/json")

        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    # 2 - login com credenciais incorretas
    def test_login_failure(self, client, app_module):
        with patch.object(app_module, "get_db") as mock_db:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchone.return_value = None
            conn.cursor.return_value = cur
            mock_db.return_value = conn

            resp = client.post("/api/login",
                               data=json.dumps({"login": "wrong", "senha": "wrong"}),
                               content_type="application/json")

        assert resp.status_code == 401
        assert resp.get_json()["success"] is False

    # 3 - logout limpa sessão
    def test_logout(self, logged_client):
        resp = logged_client.post("/api/logout")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    # 4 - rota protegida exige login
    def test_protected_route_requires_login(self, client):
        resp = client.get("/api/receitas")
        assert resp.status_code == 401
        assert "Login necessário" in resp.get_json()["error"]


class TestGetReceitas:

    def _fake_db_rows(self, rows):
        """Converte lista de dicts em rows com data_registro mockado."""
        result = []
        for r in rows:
            d = dict(r)
            d["data_registro"] = MagicMock(strftime=lambda fmt: d["data_registro"]
                                           if isinstance(d["data_registro"], str) else "2024-01-01T00:00:00")
            result.append(d)
        return result

    # 5 - listar todas as receitas
    def test_get_all_receitas(self, logged_client, app_module):
        rows = [make_receita(1), make_receita(2, nome="Pizza", tipo="salgada")]
        with patch.object(app_module, "get_db") as mock_db:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchall.return_value = self._fake_db_rows(rows)
            conn.cursor.return_value = cur
            mock_db.return_value = conn

            resp = logged_client.get("/api/receitas")

        assert resp.status_code == 200
        assert len(resp.get_json()) == 2

    # 6 - filtro por tipo=doce
    def test_filter_by_tipo_doce(self, logged_client, app_module):
        with patch.object(app_module, "get_db") as mock_db:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchall.return_value = []
            conn.cursor.return_value = cur
            mock_db.return_value = conn

            resp = logged_client.get("/api/receitas?tipo=doce")

        assert resp.status_code == 200
        call_args = cur.execute.call_args
        assert "doce" in str(call_args)

    # 7 - filtro por data_inicio
    def test_filter_by_data_inicio(self, logged_client, app_module):
        with patch.object(app_module, "get_db") as mock_db:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchall.return_value = []
            conn.cursor.return_value = cur
            mock_db.return_value = conn

            resp = logged_client.get("/api/receitas?data_inicio=2024-01-01")

        assert resp.status_code == 200
        call_args = cur.execute.call_args
        assert "2024-01-01" in str(call_args)

    # 8 - filtro por data_fim
    def test_filter_by_data_fim(self, logged_client, app_module):
        with patch.object(app_module, "get_db") as mock_db:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchall.return_value = []
            conn.cursor.return_value = cur
            mock_db.return_value = conn

            resp = logged_client.get("/api/receitas?data_fim=2024-12-31")

        assert resp.status_code == 200
        call_args = cur.execute.call_args
        assert "2024-12-31" in str(call_args)

    # 9 - busca por id (encontrada)
    def test_get_receita_by_id_found(self, logged_client, app_module):
        row_data = {
            "id": 1, "nome": "Bolo", "descricao": "Desc", "custo": 20.0,
            "tipo_receita": "doce",
            "data_registro": MagicMock(strftime=lambda fmt: "2024-01-01T00:00:00"),
        }
        with patch.object(app_module, "get_db") as mock_db:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchone.return_value = _mock_row(row_data)
            conn.cursor.return_value = cur
            mock_db.return_value = conn

            resp = logged_client.get("/api/receitas/1")

        assert resp.status_code == 200

    # 10 - busca por id (não encontrada)
    def test_get_receita_by_id_not_found(self, logged_client, app_module):
        with patch.object(app_module, "get_db") as mock_db:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchone.return_value = None
            conn.cursor.return_value = cur
            mock_db.return_value = conn

            resp = logged_client.get("/api/receitas/999")

        assert resp.status_code == 404
        assert "não encontrada" in resp.get_json()["error"]


# ---------------------------------------------------------------------------
# POST receitas
# ---------------------------------------------------------------------------

class TestCreateReceita:

    def _new_row(self):
        return _mock_row({
            "id": 1, "nome": "Bolo", "descricao": "Desc", "custo": 25.50,
            "tipo_receita": "doce",
            "data_registro": MagicMock(strftime=lambda f: "2024-01-01"),
        })

    # 11 - criar receita com sucesso
    def test_create_receita_success(self, logged_client, app_module):
        with patch.object(app_module, "get_db") as mock_db, \
             patch.object(app_module, "send_email") as mock_email:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchone.return_value = self._new_row()
            conn.cursor.return_value = cur
            mock_db.return_value = conn

            resp = logged_client.post("/api/receitas",
                                     data=json.dumps({"nome": "Bolo", "descricao": "Desc",
                                                      "custo": 25.50, "tipo_receita": "doce"}),
                                     content_type="application/json")

        assert resp.status_code == 201
        assert resp.get_json()["success"] is True
        mock_email.assert_called_once()

    # 12 - campos obrigatórios ausentes
    def test_create_receita_missing_fields(self, logged_client):
        resp = logged_client.post("/api/receitas",
                                  data=json.dumps({"nome": "Bolo"}),
                                  content_type="application/json")
        assert resp.status_code == 400
        assert "obrigatórios" in resp.get_json()["error"]

    # 13 - tipo inválido
    def test_create_receita_invalid_tipo(self, logged_client):
        resp = logged_client.post("/api/receitas",
                                  data=json.dumps({"nome": "X", "descricao": "Y",
                                                   "custo": 10, "tipo_receita": "invalido"}),
                                  content_type="application/json")
        assert resp.status_code == 400
        assert "Tipo" in resp.get_json()["error"]

    # 14 - e-mail é enviado ao criar
    def test_email_sent_on_create(self, logged_client, app_module):
        row = _mock_row({
            "id": 2, "nome": "Pudim", "descricao": "Doce", "custo": 18.0,
            "tipo_receita": "doce",
            "data_registro": MagicMock(strftime=lambda f: "2024-01-01"),
        })
        with patch.object(app_module, "get_db") as mock_db, \
             patch.object(app_module, "send_email") as mock_email:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchone.return_value = row
            conn.cursor.return_value = cur
            mock_db.return_value = conn
            mock_email.return_value = True

            logged_client.post("/api/receitas",
                               data=json.dumps({"nome": "Pudim", "descricao": "Doce",
                                                "custo": 18, "tipo_receita": "doce"}),
                               content_type="application/json")

        assert mock_email.called
        subject = mock_email.call_args[0][0]
        assert "Pudim" in subject


class TestUpdateReceita:

    def _existing_row(self):
        return _mock_row({
            "id": 1, "nome": "Old", "descricao": "Old Desc", "custo": 10.0,
            "tipo_receita": "doce",
            "data_registro": MagicMock(strftime=lambda f: "2024-01-01"),
        })

    # 15 - atualizar receita existente
    def test_update_receita_success(self, logged_client, app_module):
        existing = self._existing_row()
        with patch.object(app_module, "get_db") as mock_db, \
             patch.object(app_module, "send_email"):
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchone.side_effect = [existing, existing]
            conn.cursor.return_value = cur
            mock_db.return_value = conn

            resp = logged_client.put("/api/receitas/1",
                                     data=json.dumps({"nome": "Novo", "descricao": "Nova Desc",
                                                      "custo": 20, "tipo_receita": "salgada"}),
                                     content_type="application/json")

        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    # 16 - atualizar receita inexistente
    def test_update_receita_not_found(self, logged_client, app_module):
        with patch.object(app_module, "get_db") as mock_db:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchone.return_value = None
            conn.cursor.return_value = cur
            mock_db.return_value = conn

            resp = logged_client.put("/api/receitas/999",
                                     data=json.dumps({"nome": "X", "descricao": "Y",
                                                      "custo": 10, "tipo_receita": "doce"}),
                                     content_type="application/json")

        assert resp.status_code == 404

    # 17 - e-mail é enviado ao atualizar
    def test_email_sent_on_update(self, logged_client, app_module):
        existing = self._existing_row()
        with patch.object(app_module, "get_db") as mock_db, \
             patch.object(app_module, "send_email") as mock_email:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchone.side_effect = [existing, existing]
            conn.cursor.return_value = cur
            mock_db.return_value = conn

            logged_client.put("/api/receitas/1",
                              data=json.dumps({"nome": "Pizza", "descricao": "Desc",
                                               "custo": 35, "tipo_receita": "salgada"}),
                              content_type="application/json")

        assert mock_email.called


class TestDeleteReceita:

    # 18 - deletar receita existente
    def test_delete_receita_success(self, logged_client, app_module):
        with patch.object(app_module, "get_db") as mock_db:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchone.return_value = MagicMock()
            conn.cursor.return_value = cur
            mock_db.return_value = conn

            resp = logged_client.delete("/api/receitas/1")

        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    # 19 - deletar receita inexistente retorna 404
    def test_delete_receita_not_found(self, logged_client, app_module):
        with patch.object(app_module, "get_db") as mock_db:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchone.return_value = None
            conn.cursor.return_value = cur
            mock_db.return_value = conn

            resp = logged_client.delete("/api/receitas/999")

        assert resp.status_code == 404

class TestPdfExport:

    # 20 - PDF retorna 404 para receita inexistente
    def test_pdf_not_found(self, logged_client, app_module):
        with patch.object(app_module, "get_db") as mock_db:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchone.return_value = None
            conn.cursor.return_value = cur
            mock_db.return_value = conn

            resp = logged_client.get("/api/receitas/999/pdf")

        assert resp.status_code == 404
        assert "não encontrada" in resp.get_json()["error"]