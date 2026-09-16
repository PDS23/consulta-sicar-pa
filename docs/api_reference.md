
# API SICAR Pará (SYDLE) — Documentação Não Oficial

**Versão:** 1.1
**Status:** Documentação não oficial

Esta documentação descreve os endpoints expostos pela interface do **Sistema de Cadastro Ambiental Rural do Estado do Pará (SICAR-PA)**, baseados no motor da plataforma **SYDLE ONE**.

---

## 🔐 1. Autenticação e Segurança

### 1.1 Token de autorização

As requisições à API utilizam um token **JWT** enviado no cabeçalho HTTP `Authorization`.

```http
Authorization: Bearer <TOKEN>
```

### 1.2 Sessão Cloudflare / WAF

Downloads de arquivos binários podem exigir uma sessão válida do Cloudflare.

Nesse caso, a requisição deve conter:

* Cookie `__cf_bm`
* `Referer`
* `User-Agent`

> **Importante:** o comportamento do WAF pode variar conforme a sessão e a origem da requisição.

---

# 🔍 2. Busca Principal de Imóveis — `buscarCARPRA`

Endpoint responsável pela consulta ao **DataLake**, retornando informações gerais do imóvel, cálculos primários e o identificador interno utilizado pelos demais endpoints.

### Endpoint

```http
POST https://portal-servicos-sistemas.semas.pa.gov.br/api/1/servicedesk-embedded-servicos-sistemas/_classId/649086b520338013be9c0e2d/buscarCARPRA
```

### Método

```http
POST
```

### Headers

```http
Content-Type: application/json
Authorization: Bearer <TOKEN>
```

### Payload

```json
{
  "codigoCar": "",
  "cpfCadastrante": "",
  "cpfCnpjProprietario": "01234567890",
  "itemsPerPage": 10,
  "municipio": "",
  "nomeImovel": "",
  "obterTotal": true,
  "page": 0,
  "protocolo": ""
}
```

### Principais parâmetros

| Parâmetro             | Tipo      | Descrição                                |
| --------------------- | --------- | ---------------------------------------- |
| `codigoCar`           | `string`  | Código do CAR                            |
| `cpfCadastrante`      | `string`  | CPF do cadastrante                       |
| `cpfCnpjProprietario` | `string`  | CPF ou CNPJ do proprietário              |
| `itemsPerPage`        | `integer` | Quantidade de resultados por página      |
| `municipio`           | `string`  | Município do imóvel                      |
| `nomeImovel`          | `string`  | Nome do imóvel                           |
| `obterTotal`          | `boolean` | Solicita a quantidade total de registros |
| `page`                | `integer` | Página da consulta                       |
| `protocolo`           | `string`  | Número do protocolo                      |

### Fluxo

```text
CPF/CNPJ
   │
   ▼
buscarCARPRA
   │
   ▼
Consulta ao DataLake
   │
   ├── Dados do imóvel
   ├── Informações do proprietário
   ├── Cálculos
   └── CAR ID
```

O `CAR ID` retornado por essa consulta pode ser utilizado em chamadas posteriores, como `createDraftForm` e `baixarShapefiles`.

---

# 📋 3. Detalhamento e Compliance Ambiental — `createDraftForm`

Endpoint responsável por gerar o espelho do **Modal de Detalhes** do imóvel.

O retorno concentra informações relacionadas a:

* Passivo ambiental
* Infrações
* Restrições ambientais
* Sobreposições fundiárias
* Áreas desmatadas
* Informações do PRA
* Metadados para documentos

### Endpoint

```http
POST https://portal-servicos-sistemas.semas.pa.gov.br/api/1/servicedesk-embedded-servicos-sistemas/_classId/66901b1ac51b7731db39a904/createDraftForm?_translate=false
```

### Método

```http
POST
```

### Headers

```http
Content-Type: application/json
Authorization: Bearer <TOKEN>
```

### Dinâmica do Payload

A requisição exige os parâmetros de contexto necessários para que o motor da **SYDLE ONE** gere o formulário referente ao método:

```text
_extDadosDoImovel
```

Esse método é vinculado ao `carId` do imóvel consultado.

### Estrutura conceitual

```text
CAR ID
  │
  ▼
createDraftForm
  │
  ▼
_extDadosDoImovel
  │
  ▼
extendedMetadata.object.consultaGeral
  │
  ├── restricoesAmbientais
  ├── areasDesmatadasPos2008
  ├── descricaoDasAreasARegularizar
  └── demonstrativoPRA
```

---

## 3.1 Retorno — `consultaGeral`

Os principais dados de compliance ambiental ficam concentrados em:

```text
extendedMetadata.object.consultaGeral
```

### `restricoesAmbientais`

Array responsável por indicar possíveis sobreposições e restrições ambientais.

Pode conter informações relacionadas a:

* Assentamentos
* Terras Indígenas
* Unidades de Conservação
* Outros imóveis
* Áreas embargadas

Os valores indicam, de maneira geral, situações como:

```text
Presente
Ausente
```

---

### `areasDesmatadasPos2008`

Array contendo informações relacionadas ao desmatamento posterior a 2008.

Pode apresentar valores em hectares relacionados a:

* Reserva Legal (RL)
* Área de Preservação Permanente (APP)
* Uso Restrito
* Uso Alternativo do Solo

---

### `descricaoDasAreasARegularizar`

Representa informações relacionadas ao **Passivo Ambiental** do imóvel.

O campo permite identificar os hectares associados às áreas que precisam ser regularizadas ou recompostas.

---

### `demonstrativoPRA`

Contém metadados relacionados ao **Demonstrativo do Imóvel**, incluindo informações utilizadas para obtenção do documento em PDF.

Exemplo conceitual:

```json
{
  "id": "...",
  "name": "...",
  "url": "..."
}
```

A URL disponível nesse objeto pode ser utilizada posteriormente para obtenção do documento.

---

# 🗺️ 4. Obtenção de Links Espaciais — `baixarShapefiles`

Endpoint responsável por obter as URLs temporárias utilizadas para download das camadas geográficas associadas ao imóvel.

### Endpoint

```http
POST https://portal-servicos-sistemas.semas.pa.gov.br/api/1/servicedesk-embedded-servicos-sistemas/_classId/649086b520338013be9c0e2d/baixarShapefiles
```

### Método

```http
POST
```

### Headers

```http
Content-Type: application/json
Authorization: Bearer <TOKEN>
```

### Payload

```json
{
  "_id": "CAR_ID_AQUI"
}
```

### Fluxo

```text
CAR ID
  │
  ▼
baixarShapefiles
  │
  ▼
URLs seguras/dinâmicas
  │
  ├── Camadas do imóvel
  ├── Shapefiles
  └── Outros arquivos espaciais
```

> As URLs retornadas são destinadas à etapa posterior de download dos arquivos.

---

# ⚙️ 5. Descoberta de Ações do Processo — `getDisplayMethods`

Endpoint utilizado para **Discovery** das ações disponíveis para determinado cadastro.

A resposta informa quais métodos e ações administrativas podem estar disponíveis para um determinado objeto.

### Endpoint

```http
GET https://portal-servicos-sistemas.semas.pa.gov.br/api/1/servicedesk-embedded-servicos-sistemas/com.sydle.ui.workspaces/ONEUIAPI/getDisplayMethods
```

### Método

```http
GET
```

### Parâmetros

A requisição utiliza um JSON codificado em **URL Encoding**, enviado através do parâmetro:

```text
_body
```

Esse objeto contém o `_id` do registro e o contexto necessário para a consulta.

### Estrutura conceitual

```text
GET /getDisplayMethods
       │
       ▼
     _body
       │
       ├── _id
       └── contexto
       │
       ▼
Métodos disponíveis
```

---

## 5.1 Métodos comuns

| Método                 | Descrição                                                 |
| ---------------------- | --------------------------------------------------------- |
| `_extDadosDoImovel`    | Consulta os dados detalhados do imóvel                    |
| `visualizarProcesso`   | Acessa informações de tramitação do processo              |
| `visualizarDocumentos` | Acessa o acervo de documentos                             |
| `retificarCAR`         | Disponibiliza a funcionalidade de retificação do cadastro |

> A disponibilidade dos métodos pode variar de acordo com o estado e o contexto do cadastro consultado.

---

# ⬇️ 6. Download de Arquivos Binários — ZIP/PDF

Essa é a etapa final para obtenção dos arquivos físicos relacionados ao imóvel.

Pode ser utilizada para baixar:

* Shapefiles
* Arquivos ZIP
* Demonstrativos em PDF
* Outros arquivos disponibilizados pela plataforma

As URLs devem ser obtidas previamente através de:

```text
baixarShapefiles
```

ou do campo:

```text
demonstrativoPRA.url
```

---

## 6.1 Requisição

### Método

```http
GET
```

### URL

Utilizar a URL retornada pelos endpoints anteriores.

---

## 6.2 Headers obrigatórios

Em determinados downloads, **não deve ser utilizado**:

```http
Authorization: Bearer <TOKEN>
```

A presença desse header pode resultar em:

```text
invalid_client
```

Em seu lugar, o download pode exigir:

```http
Cookie: __cf_bm=...
Referer: ...
User-Agent: ...
```

### Exemplo conceitual

```http
GET <URL_DO_ARQUIVO>
Cookie: __cf_bm=...
Referer: https://portal-servicos-sistemas.semas.pa.gov.br/
User-Agent: Mozilla/5.0 ...
```

---

# 📦 7. Comportamento das Respostas

## 7.1 Download realizado com sucesso

Quando autorizado, o servidor retorna o conteúdo binário.

### ZIP

```http
HTTP/1.1 200 OK
Content-Type: application/x-zip-compressed
```

### PDF

```http
HTTP/1.1 200 OK
Content-Type: application/pdf
```

---

## 7.2 Bloqueio pelo WAF / Cloudflare

O status HTTP nem sempre indica que o download foi realizado corretamente.

Pode ocorrer um:

```http
HTTP/1.1 200 OK
```

mesmo quando o conteúdo retornado é uma página HTML do Cloudflare.

Também pode ocorrer:

```http
HTTP/1.1 401 Unauthorized
```

### Portanto, recomenda-se validar:

1. Status HTTP
2. `Content-Type`
3. Tamanho do arquivo
4. Assinatura/magic bytes do arquivo
5. Conteúdo retornado

Exemplo de validação conceitual:

```text
HTTP 200
   │
   ├── Content-Type = application/pdf
   │       └── PDF válido
   │
   ├── Content-Type = application/x-zip-compressed
   │       └── ZIP válido
   │
   └── Content-Type = text/html
           └── Possível bloqueio Cloudflare
```

---

# 🔄 8. Fluxo Geral da API

O fluxo completo de consulta pode ser representado da seguinte forma:

```text
┌─────────────────────┐
│     CPF / CNPJ      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    buscarCARPRA     │
└──────────┬──────────┘
           │
           ▼
      ┌─────────┐
      │ CAR ID  │
      └────┬────┘
           │
     ┌─────┴───────────────┐
     │                     │
     ▼                     ▼
┌──────────────┐    ┌─────────────────┐
│createDraftForm│    │baixarShapefiles│
└──────┬───────┘    └────────┬────────┘
       │                      │
       ▼                      ▼
┌───────────────┐      ┌──────────────┐
│Compliance     │      │URLs espaciais│
│Ambiental      │      │dinâmicas     │
└───────────────┘      └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ Download ZIP │
                       └──────────────┘

                 ┌──────────────────┐
                 │ getDisplayMethods│
                 └────────┬─────────┘
                          │
                          ▼
                 Métodos disponíveis
```

---

# 🧩 9. Resumo dos Endpoints

| Endpoint                | Método | Finalidade                                |
| ----------------------- | -----: | ----------------------------------------- |
| `buscarCARPRA`          | `POST` | Buscar imóveis e obter o `CAR ID`         |
| `createDraftForm`       | `POST` | Consultar detalhes e compliance ambiental |
| `baixarShapefiles`      | `POST` | Obter URLs para arquivos espaciais        |
| `getDisplayMethods`     |  `GET` | Descobrir ações disponíveis no cadastro   |
| URL dinâmica de arquivo |  `GET` | Baixar ZIP/PDF                            |

---

# 🔗 10. Dependências entre os Endpoints

A utilização dos endpoints segue, em geral, esta sequência:

### 1. Localizar o imóvel

```text
buscarCARPRA
```

↓

### 2. Obter o identificador interno

```text
CAR ID
```

↓

### 3. Consultar informações ambientais

```text
createDraftForm
```

↓

### 4. Obter arquivos espaciais

```text
baixarShapefiles
```

↓

### 5. Baixar os arquivos

```text
GET <URL_DINÂMICA>
```

Paralelamente, pode-se utilizar:

```text
getDisplayMethods
```

para descobrir as ações disponíveis para o cadastro.

---

# ⚠️ 11. Observações Importantes

* Esta documentação é **não oficial**.
* Os endpoints são baseados na interface pública/integração utilizada pelo SICAR-PA e pela plataforma SYDLE ONE.
* Estruturas internas da SYDLE podem sofrer alterações sem aviso.
* URLs de download podem ser temporárias ou vinculadas a uma sessão.
* O Cloudflare pode exigir cookies e headers específicos.
* Um `HTTP 200` não garante que o arquivo tenha sido entregue corretamente.
* Recomenda-se validar o `Content-Type` e o conteúdo binário antes de salvar o arquivo.
* O token JWT utilizado nos endpoints autenticados deve ser tratado como informação sensível.
* Não compartilhe tokens, cookies de sessão ou credenciais em código público.

---

# 📌 12. Mapa Rápido da Integração

```text
                    SICAR-PA / SYDLE
                           │
                           ▼
                    ┌─────────────┐
                    │ buscarCARPRA│
                    └──────┬──────┘
                           │
                           ▼
                        CAR ID
                           │
             ┌─────────────┼──────────────┐
             │             │              │
             ▼             ▼              ▼
      createDraftForm  baixarShapefiles  getDisplayMethods
             │             │              │
             ▼             ▼              ▼
       Compliance       URLs ZIP       Ações do
        Ambiental       / arquivos      processo
                           │
                           ▼
                      GET / Download
                           │
                    ┌──────┴──────┐
                    ▼             ▼
                  ZIP            PDF
```

**Fim da documentação.**
