import zipfile

from sicar_pa.downloads import baixar_demonstrativo_pdf, gerar_zip_demonstrativos_lote


class FakeResponse:
    def __init__(self, status_code=200, content=b"", content_type=""):
        self.status_code = status_code
        self.content = content
        self.headers = {"Content-Type": content_type}


REG_COM_DEMONSTRATIVO = {
    "codigoCAR": "PA-1500107-XXXX",
    "idDemonstrativo": "pdf-1",
    "idObjetoFormulario": "form-1",
    "nomeDemonstrativo": "Demonstrativo.pdf",
}


def test_baixar_demonstrativo_pdf_retorna_none_sem_ids():
    assert baixar_demonstrativo_pdf({}, cookie_cf="", token="tok") is None


def test_baixar_demonstrativo_pdf_retorna_bytes_em_sucesso(monkeypatch):
    monkeypatch.setattr(
        "sicar_pa.downloads.requests.get",
        lambda *a, **k: FakeResponse(200, b"%PDF-conteudo", "application/pdf"),
    )
    assert baixar_demonstrativo_pdf(REG_COM_DEMONSTRATIVO, cookie_cf="cf=1", token="tok") == b"%PDF-conteudo"


def test_baixar_demonstrativo_pdf_retorna_none_quando_waf_devolve_html(monkeypatch):
    monkeypatch.setattr(
        "sicar_pa.downloads.requests.get",
        lambda *a, **k: FakeResponse(200, b"<html>bloqueado</html>", "text/html"),
    )
    assert baixar_demonstrativo_pdf(REG_COM_DEMONSTRATIVO, cookie_cf="", token="tok") is None


def test_gerar_zip_demonstrativos_lote_inclui_apenas_sucesso(monkeypatch):
    def fake_get(url, headers=None, timeout=None):
        if "form-1" in url:
            return FakeResponse(200, b"%PDF-ok", "application/pdf")
        return FakeResponse(200, b"", "text/html")

    monkeypatch.setattr("sicar_pa.downloads.requests.get", fake_get)

    sem_demonstrativo = {"codigoCAR": "PA-9999999-YYYY"}
    buffer = gerar_zip_demonstrativos_lote([REG_COM_DEMONSTRATIVO, sem_demonstrativo], cookie_cf="", token="tok")

    with zipfile.ZipFile(buffer) as zf:
        nomes = zf.namelist()
        assert nomes == ["PA-1500107-XXXX/Demonstrativo.pdf"]
