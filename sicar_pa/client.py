"""Chamadas à API oficial do SICAR-PA: busca de imóveis e dados de compliance.

Calls the documented `buscarCARPRA` and `createDraftForm` endpoints (see
docs/api_reference.md) — the same JSON endpoints the portal's own frontend
calls, no scraping involved.
"""

from typing import Any

import requests

from .config import DEFAULT_URL, URL_COMPLIANCE
from .parsing import g, normalizar_cpf_cnpj, safe_dict


def buscar_compliance_imovel(car_id: str, token: str) -> dict[str, Any]:
    """Consulta o endpoint de formulário para obter restrições e passivos do imóvel."""
    if not car_id:
        return {}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.strip()}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    payload = {
        "_checkDelegation": True,
        "classId": "694058ca43e8553082cfba91",
        "input": {
            "_checkDelegation": True,
            "_classId": "6423516bc875872c703a209a",
            "_delegationUser": None,
            "_methodIdentifier": "_extDadosDoImovel",
            "_methodName": "Dados do imóvel",
            "_objects": None,
            "_outputClass": None,
            "_refObject": {
                "_classId": "6423516bc875872c703a209a",
                "_id": str(car_id),
            },
        },
    }

    try:
        res = requests.post(URL_COMPLIANCE, json=payload, headers=headers, timeout=20)
        if res.status_code != 200:
            return {}
        json_resp = res.json()

        # O objeto raiz 'object' contém o ID_1 necessário para o download do PDF
        obj_data = json_resp.get("object", {})
        dados = obj_data.get("consultaGeral", {})

        comp_data: dict[str, Any] = {}

        for rest in dados.get("restricoesAmbientais", []):
            origem = rest.get("origem", "")
            status = rest.get("sobreposicoes", "")
            if origem:
                comp_data[f"rest_{origem}"] = status.replace("✅", "").replace("❌", "").strip()

        for desm in dados.get("areasDesmatadasPos2008", []):
            origem = desm.get("valoresReferentesAsAreasDesmatadasPos2008", "")
            area = desm.get("area", 0.0)
            if origem:
                comp_data[f"desm_{origem}"] = area

        for reg in dados.get("descricaoDasAreasARegularizar", []):
            origem = reg.get("descricaoDasAreasASeremRegularizadas", "")
            area = reg.get("totalARegularizar", 0.0)
            if origem:
                comp_data[f"passivo_{origem}"] = area

        # Captura ID_1 (formulário) + ID_2 (arquivo) necessários para baixar o PDF depois
        demo = dados.get("demonstrativoPRA", {})
        if demo and isinstance(demo, dict):
            comp_data["idDemonstrativo"] = demo.get("_id")
            comp_data["idObjetoFormulario"] = obj_data.get("_id")
            comp_data["nomeDemonstrativo"] = demo.get("name", "Demonstrativo.pdf")

        return comp_data
    except Exception:
        return {}


def extrair_atributos_registro(item_json: Any, token: str | None = None) -> dict[str, Any]:
    """Achata um registro bruto da busca em um dict plano, incluindo compliance."""
    res: dict[str, Any] = {}
    item = safe_dict(item_json)

    res["codigoCAR"] = g(item, "codigoCAR")
    res["nome"] = g(item, "nome")
    res["municipio"] = g(item, "municipio")
    res["area"] = g(item, "area")
    res["mf"] = g(item, "mf")
    res["statusCAR"] = g(item, "statusCAR")
    res["condicao"] = g(item, "condicao")

    vcar = safe_dict(g(item, "versaoDoCAR"))
    cond = safe_dict(g(vcar, "condicao"))
    res["nomeCondicaoFederal"] = g(cond, "nomeCondicaoFederal")

    res["codigoDoProtocolo"] = g(vcar, "codigoDoProtocolo")
    res["versaoDoCAR"] = g(vcar, "versaoDoCAR")
    res["cpfProtocolante"] = g(vcar, "cpfProtocolante")
    res["reciboDaVersaoURL"] = g(vcar, "reciboDaVersaoURL")
    res["carId"] = g(item, "_id")

    infocar = safe_dict(g(vcar, "informacoesCar"))
    tab_rep = g(
        safe_dict(g(infocar, "dadosPropriedadePosse")).get("formularioDominioImovelRepresent", {}),
        "tabelaImovelRepresentante",
        [],
    )
    if isinstance(tab_rep, list) and tab_rep:
        rep = safe_dict(tab_rep[0])
        res["nomeProprietario"] = g(rep, "nome")
        res["documentoProprietario"] = g(rep, "documento")
        res["tipoDominio"] = g(rep, "tipo")
    else:
        cpfs = g(vcar, "cpfProprietario", [])
        res["documentoProprietario"] = cpfs[0] if (isinstance(cpfs, list) and cpfs) else None

    if res["carId"]:
        res.update(buscar_compliance_imovel(res["carId"], token))

    return res


def buscar_sicar_completo(
    var_payload: str, valor: Any, token: str | None = None, url: str | None = None
) -> list[dict[str, Any]]:
    """Busca por CPF/CNPJ ou código do CAR e retorna cada imóvel já com compliance."""
    if not valor:
        return []
    valor_limpo = normalizar_cpf_cnpj(valor) if "cpf" in var_payload.lower() else str(valor).upper().strip()
    if not valor_limpo:
        return []

    payload = {
        "codigoCar": "",
        "cpfCadastrante": "",
        "cpfCnpjProprietario": "",
        "itemsPerPage": 10,
        "page": 0,
        "obterTotal": True,
    }
    payload[var_payload] = valor_limpo

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token.strip()}"}

    try:
        res = requests.post(url or DEFAULT_URL, json=payload, headers=headers, timeout=20)
        if res.status_code == 200:
            dados_brutos = [d for d in res.json().get("dados", []) if isinstance(d, dict)]
            return [extrair_atributos_registro(d, token) for d in dados_brutos]
    except Exception:
        pass
    return []
