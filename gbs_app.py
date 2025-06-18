import streamlit as st
import pandas as pd
import math
import io
from datetime import datetime

# --- Lógica de Cálculo de Aproveitamento e Retalhos com Sequência de Corte Real ---
def calcular_aproveitamento_e_retalhos_novo(largura_corte_mm, comprimento_corte_mm, largura_chapa_base_mm, comprimento_chapa_base_mm):
    # Dimensões da chapa base (do seu estoque)
    L_base = largura_chapa_base_mm
    C_base = comprimento_chapa_base_mm

    # Dimensões da chapa de corte da caixa
    L_corte = largura_corte_mm
    C_corte = comprimento_corte_mm

    retalhos_gerados_map = {} # Dicionário para armazenar dimensões e quantidades de retalhos

    # --- SIMULAÇÃO DA SEQUÊNCIA DE CORTE REAL (Prioriza corte no COMPRIMENTO da chapa base) ---

    # 1. Quantidade de peças que cabem ao longo do COMPRIMENTO da chapa base (C_base)
    pecas_ao_longo_comprimento = math.floor(C_base / C_corte)
    
    # 2. Quantidade de peças que cabem ao longo da LARGURA da chapa base (L_base)
    pecas_ao_longo_largura = math.floor(L_base / L_corte)

    qtd_caixas_produzidas_por_chapa = pecas_ao_longo_comprimento * pecas_ao_longo_largura

    # --- Cálculo dos Retalhos ---

    # Retalho do COMPRIMENTO (Vertical): O grande retalho gerado na ponta do comprimento da chapa
    sobra_C = C_base - (pecas_ao_longo_comprimento * C_corte)
    if sobra_C > 0.1: # Considera sobra se for maior que 0.1mm (para evitar retalhos muito pequenos por erro de float)
        # Formato LARGURA x COMPRIMENTO
        retalho_C_dim = f"{L_base:.0f}x{sobra_C:.0f}" # Largura total da chapa base x sobra de comprimento
        retalhos_gerados_map[retalho_C_dim] = retalhos_gerados_map.get(retalho_C_dim, 0) + 1 # Apenas 1 grande retalho por chapa base

    # Retalhos da LARGURA (Horizontais): Múltiplos retalhos gerados na lateral da chapa
    sobra_L = L_base - (pecas_ao_longo_largura * L_corte)
    if sobra_L > 0.1: # Considera sobra se for maior que 0.1mm
        # Formato LARGURA x COMPRIMENTO
        retalho_L_dim = f"{sobra_L:.0f}x{C_corte:.0f}"
        # A quantidade é igual ao número de peças que couberam no COMPRIMENTO
        retalhos_gerados_map[retalho_L_dim] = retalhos_gerados_map.get(retalho_L_dim, 0) + pecas_ao_longo_comprimento

    return qtd_caixas_produzidas_por_chapa, retalhos_gerados_map


# --- Configuração da Página do Streamlit (DEVE SER A PRIMEIRA COISA A SER CHAMADA) ---
st.set_page_config(layout="wide", page_title="GBS - Planejamento de Produção")

# --- Função principal do Streamlit ---
def main():
    st.title("📦 GBS - Planejamento e Controle de Produção")

    # --- Inicialização dos DataFrames na memória (st.session_state) ---
    # Estoque
    if 'df_estoque' not in st.session_state:
        st.session_state.df_estoque = pd.DataFrame(columns=[
            'Modelo_Chapa', 'Largura_m', 'Comprimento_m', 'Tipo_Papel', 'Gramatura', 
            'Quantidade_Folhas', 'Preco_Kg', 'Peso_Total_kg', 'Valor_Total_R$'
        ])
    # Pedidos (log da sessão atual)
    if 'df_pedidos' not in st.session_state: 
        st.session_state.df_pedidos = pd.DataFrame(columns=[
            'OS', 'Cliente', 'Descricao_Pedido', 'Valor_Pedido_Total_R$', 
            'Dimensao_Corte_LxC_m', 'Quantidade_Caixas', 
            'Modelo_Chapa_Pedido', 'Tipo_Papel_Pedido', 'Gramatura_Pedido', 
            'Chapas_Consumidas', 'Retalhos_Gerados_Dimensoes', 
            'Peso_Total_Pedido_kg', 'Data_Processamento'
        ])
    
    # Inicializa variáveis para o cálculo temporário do pedido
    if 'calculo_pedido_temp' not in st.session_state:
        st.session_state.calculo_pedido_temp = None

    # --- Abas do Aplicativo ---
    tab_estoque, tab_pedido, tab_relatorios = st.tabs(["Lançar Estoque", "Lançar Pedido", "Relatórios"])

    with tab_estoque:
        st.header("➕ Lançar e Visualizar Estoque")

        # --- Carregar Estoque Existente (CSV) ---
        st.subheader("Carregar Estoque Existente da Última Sessão")
        st.info("Para começar com seus dados anteriores, faça o upload do arquivo 'estoque_gbs_atualizado.csv' que você baixou na sua última sessão.")
        uploaded_file = st.file_uploader("Carregar arquivo de Estoque CSV (.csv)", type=["csv"], key="estoque_uploader")
        if uploaded_file is not None:
            try:
                st.session_state.df_estoque = pd.read_csv(uploaded_file, sep=';', decimal=',') # Considera ; como separador
                # Garante que as colunas numéricas estejam no tipo correto
                st.session_state.df_estoque['Largura_m'] = pd.to_numeric(st.session_state.df_estoque['Largura_m'], errors='coerce')
                st.session_state.df_estoque['Comprimento_m'] = pd.to_numeric(st.session_state.df_estoque['Comprimento_m'], errors='coerce')
                st.session_state.df_estoque['Gramatura'] = pd.to_numeric(st.session_state.df_estoque['Gramatura'], errors='coerce')
                st.session_state.df_estoque['Quantidade_Folhas'] = pd.to_numeric(st.session_state.df_estoque['Quantidade_Folhas'], errors='coerce')
                st.session_state.df_estoque['Preco_Kg'] = pd.to_numeric(st.session_state.df_estoque['Preco_Kg'], errors='coerce')

                # Recalcula Peso_Total_kg e Valor_Total_R$ para garantir consistência
                st.session_state.df_estoque['Peso_Total_kg'] = (
                    st.session_state.df_estoque['Largura_m'] * st.session_state.df_estoque['Comprimento_m'] * (st.session_state.df_estoque['Gramatura'] / 1000) * st.session_state.df_estoque['Quantidade_Folhas']
                )
                st.session_state.df_estoque['Valor_Total_R$'] = (
                    st.session_state.df_estoque['Peso_Total_kg'] * st.session_state.df_estoque['Preco_Kg']
                )

                st.success("Estoque carregado com sucesso! Lembre-se que este estoque é válido apenas para esta sessão.")
            except Exception as e:
                st.error(f"Erro ao carregar o arquivo CSV: {e}. Verifique o formato, o separador (deve ser ponto e vírgula) e as colunas. Confirme se os números decimais usam VÍRGULA.")
        
        st.subheader("Adicionar Novo Item ou Atualizar Quantidade")
        with st.form("form_estoque"):
            col1, col2, col3 = st.columns(3)
            with col1:
                modelo_chapa = st.text_input("Modelo da Chapa", key="estoque_modelo_input").strip()
                largura_m = st.number_input
