🇧🇷 [Leia em português](README.pt-BR.md)

# SICAR-PA Compliance Lookup

A Streamlit app that queries the **official public API behind the SICAR-PA
portal** (Sistema de Cadastro Ambiental Rural do Estado do Pará — Brazil's
state-level rural environmental registry for Pará) and turns a CPF/CNPJ,
CAR code, or a whole spreadsheet of them into a structured compliance
report: property data, land-restriction overlaps, and post-2008
deforestation/environmental-liability figures — the same numbers a human
would otherwise copy by hand from the portal's own UI, one property at a
time.

## Problem

Environmental and supply-chain compliance teams routinely need to check
dozens or hundreds of rural properties against Pará's official land
registry — ownership, legal restrictions (indigenous land, conservation
units, settlements), and how much of each property's Legal Reserve or
Permanent Preservation Area (APP) has been deforested since 2008. Doing
that one property at a time through the government portal doesn't scale
past a handful of records.

## Technical decisions

- **Official endpoint, not scraping.** The portal's own frontend (built on
  the SYDLE ONE platform) calls a documented set of JSON API endpoints —
  `buscarCARPRA`, `createDraftForm`, `baixarShapefiles`,
  `getDisplayMethods` (see [`docs/api_reference.md`](docs/api_reference.md)
  for the full reverse-engineered-from-the-network-tab reference). This
  project calls those same endpoints directly instead of scraping rendered
  HTML — faster, more reliable, and it only reads data the portal already
  exposes to any authenticated user.
- **No credentials in the code.** The portal issues a short-lived JWT to a
  logged-in browser session; there's no public token-issuing endpoint to
  automate. Rather than embed a token (which would both leak a credential
  and stop working the moment it expires), the app asks for your own
  Bearer token at runtime, pasted from your browser's dev tools — see
  *Getting a token* below.
- **CPF/CNPJ vs. CAR code as two distinct lookup modes**, because the API
  itself expects a different payload field (`cpfCnpjProprietario`,
  `cpfCadastrante`, or `codigoCar`) depending on which one you're
  searching by — the app normalizes CPF/CNPJ input (strips punctuation,
  zero-pads to 11 or 14 digits) before sending it.
- **Individual lookup and batch mode share one core function**
  (`buscar_sicar_completo`). Batch mode reads a column out of an uploaded
  spreadsheet and calls the same lookup per row, so the two modes can never
  drift apart in behavior.
- **Compliance data requires a second call per property**
  (`createDraftForm`, keyed by the internal `carId` returned from the first
  search) — the code chains the two automatically so the caller only ever
  deals with one flat result per property.

## Result

- Quick lookup: paste a CPF, CNPJ, or CAR code, get back ownership,
  restrictions, and deforestation/liability figures for every matching
  property.
- Batch mode: upload a spreadsheet, pick which column to search by and
  which fields to pull back, and get a single Excel file with one row per
  input record — plus optional bulk download of official shapefiles and
  PDF compliance statements (`Demonstrativo`) as zip packages.

## Usage example

The app supports two distinct lookup modes because the API itself expects a
different payload field for each — pick one from the dropdown, not both:

- **By CPF/CNPJ** — the property owner's or protocol filer's tax ID
  (payload field `cpfCnpjProprietario` or `cpfCadastrante`). Input is
  normalized automatically: punctuation is stripped and the value is
  zero-padded to 11 digits (CPF) or 14 (CNPJ). Use this when you're
  checking everything registered to a given person or company.
- **By CAR code** — the property's own registry code (payload field
  `codigoCar`), e.g. `PA-1500107-0000000A0000000A0000000A0000000A`
  *(fictitious — this exact format, state-municipality-hash, is what a real
  code looks like, but this one doesn't exist)*. Use this when you already
  know exactly which property you want, from a spreadsheet or a prior
  search.

Batch mode runs either lookup mode over a whole spreadsheet column — upload
a `.xlsx`/`.csv` with a column of CAR codes (or CPFs), pick which mode it
should search by, and select which result fields to pull back per row
(ownership, restrictions, post-2008 deforestation and liability figures are
independent field groups — pick only what you need to keep the output
manageable). Never point batch mode at real third-party CPFs you don't have
a legitimate reason to query — the examples above use invented values on
purpose.

### A note on ethical use

This only ever calls the same public JSON endpoints the official SICAR-PA
portal's own frontend calls, using a token you captured from your own
logged-in session — there's no scraping, no bypassing of the portal's auth,
and no access to anything an authenticated user couldn't already see one
property at a time through the UI. Treat it accordingly: don't share your
token, and don't batch-query third parties' data beyond what your actual
due-diligence work requires.

## Project structure

```
car_pa/
├── app.py              # Streamlit UI (thin entry point)
├── sicar_pa/
│   ├── config.py        # endpoints, default token, field tables
│   ├── parsing.py        # pure helpers: safe dict access, CPF/CNPJ normalization
│   ├── client.py          # search + compliance API calls
│   ├── batch.py           # spreadsheet batch processing
│   └── downloads.py       # shapefile / PDF download + zip packaging
├── docs/api_reference.md # reverse-engineered endpoint reference
├── tests/                 # unit tests (pytest)
├── requirements.txt
└── requirements-dev.txt
```

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Running the tests

```bash
pip install -r requirements-dev.txt
pytest
```

### Getting a token

1. Log in to the SICAR-PA portal in your browser.
2. Open Developer Tools → Network tab, repeat any search on the portal.
3. Find a request to `buscarCARPRA` (or similar) and copy the
   `Authorization: Bearer <token>` header value.
4. Paste just the token into the app's sidebar field. It's short-lived —
   you'll need to repeat this when it expires.

This same lookup logic is in active internal use; this repository is a
reference implementation with the credential stripped out so anyone can
reproduce the approach against their own session.
