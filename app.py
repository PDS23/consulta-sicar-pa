import io

import pandas as pd
import streamlit as st

from sicar_pa.batch import processar_lote_planilha
from sicar_pa.config import BLOCOS_CAMPOS, DEFAULT_TOKEN, DEFAULT_URL, MAPA_PAYLOAD_PARAMETROS
from sicar_pa.client import buscar_sicar_completo
from sicar_pa.downloads import baixar_camada_shapefile, gerar_zip_demonstrativos_lote, gerar_zip_shapefiles_lote, obter_urls_shapefile

st.set_page_config(page_title="Consulta SICAR Pará", layout="wide")
st.title("Sistema de Consulta Automática e Compliance - SICAR Pará")
st.markdown("Ferramenta para extração de dados espaciais, titularidade, passivos ambientais e relatórios gerenciais.")

# Inicializa as variáveis de controle no session_state para não perder dados ao clicar em "Download"
if "processed" not in st.session_state:
    st.session_state.processed = False
    st.session_state.df_final = None
    st.session_state.buf_xls = None
    st.session_state.buf_zip_shapes = None
    st.session_state.buf_zip_pdfs = None

# Idem para a consulta rápida: sem isso, clicar em qualquer botão dentro dos
# resultados (ex. baixar shapefile) dispara um rerun do Streamlit que reseta
# o estado do botão "Consultar SICAR" para False e apaga os resultados antes
# mesmo do clique ser processado.
if "resultados_rapida" not in st.session_state:
    st.session_state.resultados_rapida = None
    st.session_state.shapes_cache = {}

# Configura o estado inicial de todos os checkboxes para "False" se ainda não existirem
for bloco, campos in BLOCOS_CAMPOS.items():
    for k in campos.keys():
        if k not in st.session_state:
            st.session_state[k] = False


def set_bloco_state(bloco_nome, estado_booleano):
    """Callback dos botões de Marcar/Desmarcar Todos."""
    for k in BLOCOS_CAMPOS[bloco_nome].keys():
        st.session_state[k] = estado_booleano


# Sidebar - Configurações
st.sidebar.header("Conexão")
with st.sidebar.expander("API e Cookies", expanded=True):
    st.caption(
        "Este projeto não vem com nenhuma credencial embutida. Faça login no "
        "portal oficial do SICAR-PA no seu navegador, abra as Ferramentas do "
        "Desenvolvedor (aba Rede), repita uma busca qualquer e copie o "
        "cabeçalho `Authorization: Bearer <token>` da requisição — cole só o "
        "token abaixo. Veja docs/api_reference.md para mais detalhes."
    )
    active_token = st.text_input("Bearer Token", value=DEFAULT_TOKEN, type="password").strip()
    active_url = st.text_input("URL Busca", value=DEFAULT_URL).strip()
    active_cookie = st.text_input("Cookie (__cf_bm) para Download", value="", type="password").strip()

tab_rapida, tab_lote = st.tabs(["Consulta Rápida", "Processamento em Lote"])

# ==========================================
# ABA 1: CONSULTA RÁPIDA
# ==========================================
with tab_rapida:
    c1, c2 = st.columns([1, 2])
    var_payload = MAPA_PAYLOAD_PARAMETROS[c1.selectbox("Buscar por:", list(MAPA_PAYLOAD_PARAMETROS.keys()))]
    valor_busca = c2.text_input("Valor:")

    if st.button("Consultar SICAR", type="primary"):
        with st.spinner("Buscando dados e compliance do imóvel..."):
            st.session_state.resultados_rapida = buscar_sicar_completo(var_payload, valor_busca, active_token, active_url)
        st.session_state.shapes_cache = {}

    # Fora do bloco do botão: assim os resultados sobrevivem ao rerun disparado
    # pelos botões de download abaixo, em vez de sumir da tela a cada clique.
    resultados = st.session_state.resultados_rapida
    if resultados is None:
        pass
    elif not resultados:
        st.error("Nenhum registro encontrado.")
    else:
        st.success(f"✅ {len(resultados)} imóvel(is) encontrado(s).")
        for i, reg in enumerate(resultados, 1):
            with st.expander(f"{reg.get('nome', 'Sem Nome')} ({reg.get('codigoCAR')})", expanded=(i == 1)):
                ca, cb, cc = st.columns(3)
                ca.markdown("### Dados Gerais")
                ca.write(f"**CAR:** {reg.get('codigoCAR')}")
                ca.write(f"**Condição:** {reg.get('condicao')}")
                ca.write(f"**Área:** {reg.get('area')} ha")

                cb.markdown("### Restrições Fundiárias")
                cb.write(f"**Assentamentos:** {reg.get('rest_Assentamentos', 'N/A')}")
                cb.write(f"**Terras Indígenas:** {reg.get('rest_Terras Indígenas', 'N/A')}")
                cb.write(f"**Embargos:** {reg.get('rest_Áreas embargadas', 'N/A')}")

                cc.markdown("### Passivo (Pós-2008)")
                cc.write(f"**Desmat. em Reserva:** {reg.get('desm_Reserva Legal', 0)} ha")
                cc.write(f"**Desmat. em APP:** {reg.get('desm_Área de Preservação Permanente', 0)} ha")
                cc.write(f"**Reserva a Recompor:** {reg.get('passivo_Reserva Legal a recompor', 0)} ha")

                st.divider()
                st.write("Baixar Geometrias (Requer Cookie):")
                car_id = reg.get("carId")
                if car_id:
                    if car_id not in st.session_state.shapes_cache:
                        st.session_state.shapes_cache[car_id] = obter_urls_shapefile(car_id, active_token)
                    shapes = st.session_state.shapes_cache[car_id]
                    for shp in shapes[:5]:
                        if st.button(f"📥 {shp['nomeArquivo']}", key=f"dl_{shp['nomeArquivo']}_{i}"):
                            bin_data = baixar_camada_shapefile(shp["url"], active_cookie)
                            if bin_data:
                                st.download_button("Salvar", bin_data, shp["nomeArquivo"], key=f"save_{shp['nomeArquivo']}_{i}")
                            else:
                                st.error("Erro WAF. Verifique seu Cookie Cloudflare.")

# ==========================================
# ABA 2: LOTE E COMPLIANCE
# ==========================================
with tab_lote:
    uploaded_file = st.file_uploader("Subir Planilha (.xlsx/.csv)", type=["xlsx", "csv"])
    if uploaded_file:
        df_input = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)

        c1, c2 = st.columns(2)
        coluna_busca = c1.selectbox("Coluna de Busca", df_input.columns)
        var_lote = MAPA_PAYLOAD_PARAMETROS[c2.selectbox("Tipo de Dado", list(MAPA_PAYLOAD_PARAMETROS.keys()))]

        st.markdown("### Seleção de Campos para a Planilha Final")

        campos_selecionados_finais = []
        for bloco, campos in BLOCOS_CAMPOS.items():
            with st.expander(bloco, expanded=True):
                btn_col1, btn_col2, _ = st.columns([2, 2, 6])
                btn_col1.button("Marcar Todos", key=f"m_{bloco}", on_click=set_bloco_state, args=(bloco, True))
                btn_col2.button("Desmarcar Todos", key=f"d_{bloco}", on_click=set_bloco_state, args=(bloco, False))

                for k, nome in campos.items():
                    if st.checkbox(nome, key=k):
                        campos_selecionados_finais.append(k)

        st.markdown("### Downloads de Arquivos em Lote")
        col_chk1, col_chk2 = st.columns(2)
        baixar_shapes = col_chk1.checkbox("Gerar pacote ZIP com os **Shapefiles** dos imóveis", value=False)
        baixar_pdfs = col_chk2.checkbox("Gerar pacote ZIP com os **Demonstrativos (PDF)** dos imóveis", value=False)

        if st.button("Processar Lote", type="primary", use_container_width=True):
            bar = st.progress(0)
            txt = st.empty()

            def cb_busca(a, t, val):
                bar.progress(a / t)
                txt.text(f"Consultando {a}/{t}: {val}")

            with st.spinner("Extraindo Dados e Compliance..."):
                df_final, regs_brutos = processar_lote_planilha(
                    df_input, coluna_busca, var_lote, campos_selecionados_finais, active_token, active_url, cb_busca
                )

            # --- ARMAZENA TUDO NO CACHE DO NAVEGADOR ---
            st.session_state.df_final = df_final

            buf_xls = io.BytesIO()
            df_final.to_excel(buf_xls, index=False)
            buf_xls.seek(0)
            st.session_state.buf_xls = buf_xls

            if baixar_shapes and regs_brutos:
                def cb_shp(a, t, car):
                    bar.progress(a / t)
                    txt.text(f"Baixando Mapas {a}/{t}: {car}")

                with st.spinner("Compactando Shapefiles..."):
                    st.session_state.buf_zip_shapes = gerar_zip_shapefiles_lote(regs_brutos, active_cookie, active_token, cb_shp)
            else:
                st.session_state.buf_zip_shapes = None

            if baixar_pdfs and regs_brutos:
                def cb_pdf(a, t, car):
                    bar.progress(a / t)
                    txt.text(f"Baixando PDFs {a}/{t}: {car}")

                with st.spinner("Baixando Demonstrativos Oficiais..."):
                    st.session_state.buf_zip_pdfs = gerar_zip_demonstrativos_lote(regs_brutos, active_cookie, active_token, cb_pdf)
            else:
                st.session_state.buf_zip_pdfs = None

            st.session_state.processed = True

        # --- EXIBE OS BOTÕES DE DOWNLOAD FORA DO ESCOPO DE PROCESSAMENTO ---
        # Isso garante que se o usuário clicar num botão, a página não vai se resetar e "esquecer" os dados
        if st.session_state.get("processed", False):
            st.success("✅ Processamento em lote finalizado com sucesso!")
            st.dataframe(st.session_state.df_final.head(10), use_container_width=True)

            col_dl1, col_dl2, col_dl3 = st.columns(3)

            with col_dl1:
                st.download_button(
                    label="📊 Baixar Planilha Final (Excel)",
                    data=st.session_state.buf_xls,
                    file_name="Compliance_SICAR.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

            if st.session_state.get("buf_zip_shapes"):
                with col_dl2:
                    st.download_button(
                        label="🗺️ Baixar Pacote Shapefiles (.zip)",
                        data=st.session_state.buf_zip_shapes,
                        file_name="Shapefiles_SICAR.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )

            if st.session_state.get("buf_zip_pdfs"):
                with col_dl3:
                    st.download_button(
                        label="📄 Baixar Demonstrativos (.zip)",
                        data=st.session_state.buf_zip_pdfs,
                        file_name="Demonstrativos_SICAR.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )
