🇺🇸 [Read in English](README.md)

# Consulta de Compliance SICAR-PA

Um app Streamlit que consulta a **API pública oficial por trás do portal
SICAR-PA** (Sistema de Cadastro Ambiental Rural do Estado do Pará) e
transforma um CPF/CNPJ, código de CAR, ou uma planilha inteira deles, em um
relatório estruturado de compliance: dados do imóvel, sobreposições com
restrições fundiárias e números de desmatamento/passivo ambiental pós-2008
— os mesmos dados que uma pessoa copiaria manualmente da interface do
portal, um imóvel de cada vez.

## Problema

Equipes de compliance ambiental e de cadeia de suprimentos precisam checar
rotineiramente dezenas ou centenas de imóveis rurais contra o cadastro
oficial do Pará — titularidade, restrições legais (terra indígena, unidade
de conservação, assentamento) e quanto da Reserva Legal ou da Área de
Preservação Permanente (APP) de cada imóvel foi desmatado desde 2008. Fazer
isso um imóvel de cada vez pelo portal do governo não escala além de um
punhado de registros.

## Decisões técnicas

- **Endpoint oficial, não scraping.** O próprio frontend do portal
  (construído sobre a plataforma SYDLE ONE) chama um conjunto documentado
  de endpoints JSON — `buscarCARPRA`, `createDraftForm`,
  `baixarShapefiles`, `getDisplayMethods` (veja
  [`docs/api_reference.md`](docs/api_reference.md) para a referência
  completa, obtida a partir da aba de rede do navegador). Este projeto
  chama esses mesmos endpoints diretamente em vez de raspar HTML
  renderizado — mais rápido, mais confiável, e só lê dados que o portal já
  expõe a qualquer usuário autenticado.
- **Nenhuma credencial no código.** O portal emite um JWT de curta duração
  para uma sessão logada no navegador; não existe endpoint público para
  emitir token de forma automatizada. Em vez de embutir um token (o que
  vazaria uma credencial e pararia de funcionar assim que ele expirasse), o
  app pede seu próprio Bearer token em tempo de execução, colado a partir
  das ferramentas de desenvolvedor do navegador — veja *Obtendo um token*
  abaixo.
- **CPF/CNPJ e código do CAR como dois modos de busca distintos**, porque a
  própria API espera um campo de payload diferente (`cpfCnpjProprietario`,
  `cpfCadastrante` ou `codigoCar`) dependendo de qual você está buscando —
  o app normaliza a entrada de CPF/CNPJ (remove pontuação, zero-preenche
  para 11 ou 14 dígitos) antes de enviar.
- **Busca individual e modo lote compartilham uma função central**
  (`buscar_sicar_completo`). O modo lote lê uma coluna de uma planilha
  enviada e chama a mesma busca por linha, então os dois modos nunca
  divergem em comportamento.
- **Dados de compliance exigem uma segunda chamada por imóvel**
  (`createDraftForm`, indexada pelo `carId` interno retornado na primeira
  busca) — o código encadeia as duas automaticamente, então quem chama só
  lida com um resultado plano por imóvel.

## Resultado

- Busca rápida: cole um CPF, CNPJ ou código de CAR e receba titularidade,
  restrições e números de desmatamento/passivo de cada imóvel encontrado.
- Modo lote: suba uma planilha, escolha por qual coluna buscar e quais
  campos trazer de volta, e receba um único Excel com uma linha por
  registro de entrada — mais download opcional em lote dos shapefiles
  oficiais e dos demonstrativos de compliance em PDF (`Demonstrativo`)
  como pacotes zip.

## Exemplo de uso

O app oferece dois modos de busca distintos porque a própria API espera um
campo de payload diferente para cada um — escolha um no dropdown, não os
dois:

- **Por CPF/CNPJ** — o documento do proprietário ou do protocolante
  (campo de payload `cpfCnpjProprietario` ou `cpfCadastrante`). A entrada é
  normalizada automaticamente: pontuação é removida e o valor é
  zero-preenchido para 11 dígitos (CPF) ou 14 (CNPJ). Use quando quiser
  checar tudo registrado em nome de uma pessoa ou empresa.
- **Por código do CAR** — o código próprio de cadastro do imóvel (campo de
  payload `codigoCar`), ex. `PA-1500107-0000000A0000000A0000000A0000000A`
  *(fictício — esse formato exato, estado-município-hash, é como um código
  real se parece, mas este aqui não existe)*. Use quando já souber
  exatamente qual imóvel quer, vindo de uma planilha ou busca anterior.

O modo lote roda qualquer um dos dois modos de busca sobre uma coluna
inteira de planilha — suba um `.xlsx`/`.csv` com uma coluna de códigos de
CAR (ou CPFs), escolha por qual modo buscar, e selecione quais campos de
resultado trazer por linha (titularidade, restrições, desmatamento pós-2008
e passivo são grupos de campos independentes — marque só o que precisar
para manter a saída gerenciável). Nunca aponte o modo lote para CPFs reais
de terceiros sem um motivo legítimo — os exemplos acima usam valores
inventados de propósito.

### Uma nota sobre uso ético

Isso só chama os mesmos endpoints JSON públicos que o próprio frontend do
portal SICAR-PA chama, usando um token capturado da sua própria sessão
logada — não há scraping, nem bypass da autenticação do portal, nem acesso
a nada que um usuário autenticado já não pudesse ver um imóvel de cada vez
pela interface. Trate de acordo: não compartilhe seu token, e não faça
consultas em lote sobre dados de terceiros além do que seu trabalho de
due diligence realmente exige.

## Estrutura do projeto

```
car_pa/
├── app.py              # UI Streamlit (entry point fino)
├── sicar_pa/
│   ├── config.py        # endpoints, token padrão, tabelas de campos
│   ├── parsing.py        # helpers puros: acesso seguro a dict, normalização de CPF/CNPJ
│   ├── client.py          # chamadas de busca + compliance na API
│   ├── batch.py           # processamento em lote de planilha
│   └── downloads.py       # download de shapefile/PDF + empacotamento em zip
├── docs/api_reference.md # referência de endpoints reverso-engenheirada
├── tests/                 # testes unitários (pytest)
├── requirements.txt
└── requirements-dev.txt
```

## Rodando o projeto

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Rodando os testes

```bash
pip install -r requirements-dev.txt
pytest
```

### Obtendo um token

1. Faça login no portal SICAR-PA no seu navegador.
2. Abra as Ferramentas do Desenvolvedor → aba Rede, repita uma busca
   qualquer no portal.
3. Encontre uma requisição para `buscarCARPRA` (ou similar) e copie o
   valor do cabeçalho `Authorization: Bearer <token>`.
4. Cole só o token no campo da sidebar do app. Ele é de curta duração —
   você vai precisar repetir isso quando expirar.

Essa mesma lógica de consulta está em uso interno ativo; este repositório é
uma implementação de referência com a credencial removida, para que
qualquer pessoa possa reproduzir a abordagem contra sua própria sessão.
