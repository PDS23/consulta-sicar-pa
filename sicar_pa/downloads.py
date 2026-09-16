"""Download de shapefiles e demonstrativos PDF, individual e em lote (zip)."""

import io
import time
import zipfile
from typing import Any, Callable

import requests

from .config import URL_BAIXAR_SHAPEFILES

ProgressCallback = Callable[[int, int, str], None]


def obter_urls_shapefile(car_id_raiz: str, token: str) -> list[dict[str, Any]]:
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token.strip()}"}
    try:
        res = requests.post(URL_BAIXAR_SHAPEFILES, json={"_id": str(car_id_raiz)}, headers=headers, timeout=20)
        if res.status_code == 200 and isinstance(res.json(), list):
            return res.json()
    except Exception:
        pass
    return []


def baixar_camada_shapefile(url_download: str, cookie_cf: str) -> bytes | None:
    headers = {
        "accept": "*/*",
        "referer": "https://portal-servicos-sistemas.semas.pa.gov.br/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    if cookie_cf:
        headers["cookie"] = cookie_cf.strip()
    try:
        res = requests.get(url_download, headers=headers, timeout=30)
        if res.status_code == 200 and "zip" in res.headers.get("Content-Type", ""):
            return res.content
    except Exception:
        pass
    return None


def gerar_zip_shapefiles_lote(
    registros: list[dict[str, Any]], cookie_cf: str, token: str, progress_callback: ProgressCallback | None = None
) -> io.BytesIO:
    buffer = io.BytesIO()
    total = len(registros)
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_mestre:
        for idx, reg in enumerate(registros, 1):
            car_id = reg.get("carId")
            codigo_car = str(reg.get("codigoCAR") or f"imovel_{idx}").replace("/", "_")
            if progress_callback:
                progress_callback(idx, total, f"Shapes: {codigo_car}")
            if not car_id:
                continue

            urls = obter_urls_shapefile(car_id, token)
            for arq in urls:
                link = arq.get("url")
                if not link:
                    continue
                bin_data = baixar_camada_shapefile(link, cookie_cf)
                if bin_data:
                    zip_mestre.writestr(f"{codigo_car}/{arq.get('nomeArquivo')}", bin_data)
            time.sleep(0.3)
    buffer.seek(0)
    return buffer


def gerar_zip_demonstrativos_lote(
    registros: list[dict[str, Any]], cookie_cf: str, token: str, progress_callback: ProgressCallback | None = None
) -> io.BytesIO:
    """Baixa os Demonstrativos em PDF e compacta em um zip único.

    Requer Bearer token + cookie Cloudflare (__cf_bm) — sem os dois o WAF
    devolve uma página HTML em vez do PDF, por isso a checagem de Content-Type.
    """
    buffer = io.BytesIO()
    total = len(registros)

    headers = {
        "accept": "*/*",
        "referer": "https://portal-servicos-sistemas.semas.pa.gov.br/consulta-geral",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "authorization": f"Bearer {token.strip()}",
    }
    if cookie_cf:
        headers["cookie"] = cookie_cf.strip()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_mestre:
        for idx, reg in enumerate(registros, 1):
            file_id = reg.get("idDemonstrativo")
            form_id = reg.get("idObjetoFormulario")
            nome_arquivo = str(reg.get("nomeDemonstrativo", f"Demonstrativo_{idx}.pdf")).replace("/", "_")
            codigo_car = str(reg.get("codigoCAR") or f"imovel_{idx}").replace("/", "_")

            if progress_callback:
                progress_callback(idx, total, f"Demonstrativo: {codigo_car}")

            if file_id and form_id:
                url_download = (
                    "https://portal-servicos-sistemas.semas.pa.gov.br/api/1/"
                    "servicedesk-embedded-servicos-sistemas/_classId/694058ca43e8553082cfba91/"
                    f"_download/{form_id}/{file_id}"
                )
                try:
                    res = requests.get(url_download, headers=headers, timeout=30)
                    tipo_conteudo = res.headers.get("Content-Type", "")
                    if res.status_code == 200 and "pdf" in tipo_conteudo:
                        zip_mestre.writestr(f"{codigo_car}/{nome_arquivo}", res.content)
                except Exception as e:
                    print(f"Erro ao baixar PDF de {codigo_car}: {e}")
            time.sleep(0.3)
    buffer.seek(0)
    return buffer
