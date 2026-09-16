"""Testa o app Streamlit de ponta a ponta com AppTest (sem rede, sem navegador).

Cobre a regressão em que clicar no botão de download de shapefile disparava
um rerun que apagava os resultados da Consulta Rápida antes do download
acontecer, porque eles só existiam dentro do bloco `if st.button(...)`.
"""

from streamlit.testing.v1 import AppTest

REG_FAKE = {
    "codigoCAR": "PA-1500107-XXXX",
    "nome": "Fazenda Teste",
    "condicao": "Ativo",
    "area": 42.0,
    "carId": "car-123",
}

SHAPE_FAKE = {"nomeArquivo": "area_imovel.zip", "url": "https://example.org/shape.zip"}


def _app_com_busca_mockada(monkeypatch):
    monkeypatch.setattr("sicar_pa.client.buscar_sicar_completo", lambda *a, **k: [REG_FAKE])
    monkeypatch.setattr("sicar_pa.downloads.obter_urls_shapefile", lambda *a, **k: [SHAPE_FAKE])
    monkeypatch.setattr("sicar_pa.downloads.baixar_camada_shapefile", lambda *a, **k: b"fake-zip-bytes")
    return AppTest.from_file("../app.py", default_timeout=15)


def test_consulta_rapida_exibe_resultado_apos_busca(monkeypatch):
    at = _app_com_busca_mockada(monkeypatch)
    at.run()
    at.button[0].click().run()  # botão "Consultar SICAR"

    assert not at.exception
    assert any("Fazenda Teste" in e.label for e in at.expander)


def test_resultados_sobrevivem_ao_clique_no_botao_de_download(monkeypatch):
    """Regressão: antes da correção, esse segundo clique apagava os resultados."""
    at = _app_com_busca_mockada(monkeypatch)
    at.run()
    at.button[0].click().run()  # busca

    assert any("Fazenda Teste" in e.label for e in at.expander)

    at.button[1].click().run()  # botão "📥 area_imovel.zip"

    assert not at.exception
    assert any("Fazenda Teste" in e.label for e in at.expander)
    assert any(db.label == "Salvar" for db in at.download_button)
