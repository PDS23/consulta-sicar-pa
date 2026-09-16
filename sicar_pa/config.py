"""Endpoints e tabelas de campos da API do portal SICAR-PA.

Ver docs/api_reference.md para a referência completa dos endpoints,
obtida a partir da aba de rede do portal oficial.
"""

# O portal emite um JWT Bearer de curta duração para uma sessão logada; não
# existe endpoint público para emitir token, então este projeto nunca embute
# um token real aqui — ele é colado em runtime pelo usuário na sidebar do app.
DEFAULT_TOKEN = ""
DEFAULT_URL = "https://portal-servicos-sistemas.semas.pa.gov.br/api/1/servicedesk-embedded-servicos-sistemas/_classId/649086b520338013be9c0e2d/buscarCARPRA"
URL_BAIXAR_SHAPEFILES = "https://portal-servicos-sistemas.semas.pa.gov.br/api/1/servicedesk-embedded-servicos-sistemas/_classId/649086b520338013be9c0e2d/baixarShapefiles"
URL_COMPLIANCE = "https://portal-servicos-sistemas.semas.pa.gov.br/api/1/servicedesk-embedded-servicos-sistemas/_classId/66901b1ac51b7731db39a904/createDraftForm?_translate=false"

BLOCOS_CAMPOS: dict[str, dict[str, str]] = {
    "Dados Gerais do Imovel": {
        "codigoCAR": "Codigo do CAR",
        "nome": "Nome do Imovel",
        "municipio": "Municipio",
        "ibgecode": "Codigo IBGE",
        "area": "Area Declarada (ha)",
        "mf": "Modulos Fiscais (MF)",
        "statusCAR": "Status do CAR",
        "condicao": "Condicao da Analise",
        "nomeCondicaoFederal": "Condicao no SICAR Federal",
    },
    "Protocolo e Recibo Oficial": {
        "codigoDoProtocolo": "Numero do Protocolo",
        "versaoDoCAR": "Versao do CAR",
        "dataProtocolo": "Data do Protocolo",
        "cpfProtocolante": "CPF do Protocolante",
        "reciboDaVersaoURL": "URL Recibo PDF Oficial",
        "carId": "ID Interno do Imovel (carId)",
    },
    "Proprietarios e Possuidores": {
        "nomeProprietario": "Nome do Titular",
        "documentoProprietario": "CPF/CNPJ do Titular",
        "tipoDominio": "Tipo de Vinculo",
        "emailProprietario": "E-mail de Contato",
    },
    "Compliance: Restricoes e Malha Fundiaria": {
        "rest_Assentamentos": "Sobreposicao: Assentamentos",
        "rest_Terras Indígenas": "Sobreposicao: Terras Indigenas",
        "rest_Unidades de Conservação": "Sobreposicao: Unid. Conservacao",
        "rest_Outros Imóveis Rurais": "Sobreposicao: Outros Imoveis",
        "rest_Áreas embargadas": "Sobreposicao: Areas Embargadas",
    },
    "Compliance: Passivo e Desmatamento Pos-2008": {
        "desm_Reserva Legal": "Desmat. Pos-2008: Reserva Legal (ha)",
        "desm_Área de Preservação Permanente": "Desmat. Pos-2008: APP (ha)",
        "desm_Área de Uso Restrito": "Desmat. Pos-2008: Uso Restrito (ha)",
        "desm_Área fora de RL, APP e AUR": "Desmat. Pos-2008: Area Alternativa (ha)",
        "passivo_Balanço de reserva legal": "A Regularizar: Balanco RL (ha)",
        "passivo_Reserva Legal a recompor": "A Regularizar: RL a recompor (ha)",
        "passivo_Área de Preservação Permanente a recompor": "A Regularizar: APP a recompor (ha)",
        "passivo_Área de Uso Restrito a recompor": "A Regularizar: Uso Restrito a recompor (ha)",
    },
}

# A API espera um nome de campo de payload diferente dependendo do modo de
# busca escolhido — este mapa traduz a opção exibida na UI para esse campo.
MAPA_PAYLOAD_PARAMETROS: dict[str, str] = {
    "Codigo do CAR": "codigoCar",
    "CPF/CNPJ do Proprietario": "cpfCnpjProprietario",
    "CPF do Cadastrante/Protocolante": "cpfCadastrante",
}
