from sicar_pa.client import buscar_sicar_completo, extrair_atributos_registro
from sicar_pa.config import DEFAULT_URL, URL_COMPLIANCE


class FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.headers = {}

    def json(self):
        return self._json_data


IMOVEL_BRUTO = {
    "_id": "car-123",
    "codigoCAR": "PA-1500107-XXXX",
    "nome": "Fazenda Exemplo",
    "municipio": "Belém",
    "area": 120.5,
    "statusCAR": "Ativo",
    "condicao": "Pendente",
    "versaoDoCAR": {
        "codigoDoProtocolo": "PROTO-1",
        "cpfProtocolante": "12345678901",
        "condicao": {"nomeCondicaoFederal": "Ativo"},
    },
}

COMPLIANCE_RESPONSE = {
    "object": {
        "_id": "form-1",
        "consultaGeral": {
            "restricoesAmbientais": [{"origem": "Assentamentos", "sobreposicoes": "❌ Não"}],
            "areasDesmatadasPos2008": [{"valoresReferentesAsAreasDesmatadasPos2008": "Reserva Legal", "area": 3.2}],
            "descricaoDasAreasARegularizar": [],
            "demonstrativoPRA": {"_id": "pdf-1", "name": "Demonstrativo.pdf"},
        },
    }
}


def test_extrair_atributos_registro_sem_compliance_quando_sem_car_id():
    reg = extrair_atributos_registro({"codigoCAR": "PA-000", "nome": "Sem ID"}, token="tok")
    assert reg["codigoCAR"] == "PA-000"
    assert reg["carId"] is None
    assert "rest_Assentamentos" not in reg


def test_extrair_atributos_registro_inclui_compliance(monkeypatch):
    def fake_post(url, json=None, headers=None, timeout=None):
        assert url == URL_COMPLIANCE
        return FakeResponse(200, COMPLIANCE_RESPONSE)

    monkeypatch.setattr("sicar_pa.client.requests.post", fake_post)

    reg = extrair_atributos_registro(IMOVEL_BRUTO, token="tok")

    assert reg["codigoCAR"] == "PA-1500107-XXXX"
    assert reg["carId"] == "car-123"
    assert reg["rest_Assentamentos"] == "Não"
    assert reg["desm_Reserva Legal"] == 3.2
    assert reg["idDemonstrativo"] == "pdf-1"
    assert reg["idObjetoFormulario"] == "form-1"


def test_buscar_sicar_completo_retorna_lista_vazia_sem_valor():
    assert buscar_sicar_completo("codigoCar", "", token="tok") == []


def test_buscar_sicar_completo_encadeia_busca_e_compliance(monkeypatch):
    def fake_post(url, json=None, headers=None, timeout=None):
        if url == DEFAULT_URL:
            return FakeResponse(200, {"dados": [IMOVEL_BRUTO]})
        if url == URL_COMPLIANCE:
            return FakeResponse(200, COMPLIANCE_RESPONSE)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr("sicar_pa.client.requests.post", fake_post)

    resultados = buscar_sicar_completo("codigoCar", "PA-1500107-XXXX", token="tok")

    assert len(resultados) == 1
    assert resultados[0]["codigoCAR"] == "PA-1500107-XXXX"
    assert resultados[0]["rest_Assentamentos"] == "Não"


def test_buscar_sicar_completo_retorna_vazio_em_erro_http(monkeypatch):
    monkeypatch.setattr("sicar_pa.client.requests.post", lambda *a, **k: FakeResponse(500, {}))
    assert buscar_sicar_completo("codigoCar", "PA-1500107-XXXX", token="tok") == []
