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
                largura_m = st.number_input("Largura da Chapa (m)", min_value=0.001, format="%.3f", key="estoque_largura_input")
            with col2:
                comprimento_m = st.number_input("Comprimento da Chapa (m)", min_value=0.001, format="%.3f", key="estoque_comprimento_input")
                tipo_papel = st.text_input("Tipo de Papel (ex: Onda C)", key="estoque_tipo_input").strip()
            with col3:
                gramatura = st.number_input("Gramatura (g/m²)", min_value=1, value=370, key="estoque_gramatura_input")
                quantidade = st.number_input("Quantidade de Folhas", min_value=0, value=0, key="estoque_quantidade_input") 
                preco_kg = st.number_input("Preço por Kg (R$)", min_value=0.01, format="%.2f", key="estoque_preco_input")

            adicionar_estoque_btn = st.form_submit_button("Adicionar/Atualizar Item no Estoque")
            
            if adicionar_estoque_btn:
                if not modelo_chapa or not tipo_papel or largura_m <= 0 or comprimento_m <= 0 or gramatura <= 0 or preco_kg <= 0:
                    st.error("Por favor, preencha todos os campos obrigatórios do estoque corretamente (Modelo, Dimensões, Tipo, Gramatura, Preço Kg).")
                else:
                    # Calcula peso_m2_kg automaticamente da gramatura
                    peso_m2_kg_calc = gramatura / 1000 
                    
                    # Calcula Peso_Total_kg e Valor_Total_R$ para o novo item
                    area_chapa_m2 = largura_m * comprimento_m
                    peso_total_item_kg = area_chapa_m2 * peso_m2_kg_calc * quantidade
                    valor_total_item_rs = peso_total_item_kg * preco_kg

                    item_existente_idx = st.session_state.df_estoque[
                        (st.session_state.df_estoque['Modelo_Chapa'] == modelo_chapa) &
                        (st.session_state.df_estoque['Tipo_Papel'] == tipo_papel) &
                        (st.session_state.df_estoque['Gramatura'] == gramatura)
                    ].index

                    if not item_existente_idx.empty:
                        # Atualiza a quantidade e recalcula pesos/valores
                        st.session_state.df_estoque.loc[item_existente_idx, 'Quantidade_Folhas'] += quantidade
                        # Recalcula pesos/valores para o item atualizado
                        existing_qty = st.session_state.df_estoque.loc[item_existente_idx, 'Quantidade_Folhas'].iloc[0]
                        st.session_state.df_estoque.loc[item_existente_idx, 'Peso_Total_kg'] = area_chapa_m2 * peso_m2_kg_calc * existing_qty
                        st.session_state.df_estoque.loc[item_existente_idx, 'Valor_Total_R$'] = st.session_state.df_estoque.loc[item_existente_idx, 'Peso_Total_kg'] * preco_kg
                        st.success(f"Quantidade do modelo '{modelo_chapa}' ({largura_m}x{comprimento_m}m, {gramatura}g/m²) atualizada para {existing_qty} folhas.")
                    else:
                        # Adiciona novo item
                        novo_item = pd.DataFrame([{
                            'Modelo_Chapa': modelo_chapa,
                            'Largura_m': largura_m,
                            'Comprimento_m': comprimento_m,
                            'Tipo_Papel': tipo_papel,
                            'Gramatura': gramatura,
                            'Quantidade_Folhas': quantidade,
                            'Preco_Kg': preco_kg,
                            'Peso_Total_kg': peso_total_item_kg,
                            'Valor_Total_R$': valor_total_item_rs
                        }])
                        st.session_state.df_estoque = pd.concat([st.session_state.df_estoque, novo_item], ignore_index=True)
                        st.success(f"Item de estoque {modelo_chapa} adicionado com sucesso!")
                    
                    st.session_state.df_estoque = st.session_state.df_estoque.sort_values(by=['Modelo_Chapa', 'Tipo_Papel', 'Gramatura']).reset_index(drop=True)


        st.subheader("Estoque Atual na Memória:")
        if not st.session_state.df_estoque.empty:
            # Calcular totais para exibição na tabela
            df_estoque_display = st.session_state.df_estoque.copy()
            total_area_m2_estoque = (df_estoque_display['Largura_m'] * df_estoque_display['Comprimento_m'] * df_estoque_display['Quantidade_Folhas']).sum()
            total_peso_estoque_kg = df_estoque_display['Peso_Total_kg'].sum()
            total_valor_estoque_rs = df_estoque_display['Valor_Total_R$'].sum()

            # Adicionar linha de totais na tabela para exibição na tela
            df_estoque_display.loc[''] = '' # Linha em branco para separar
            df_estoque_display.loc['Total Geral'] = {
                'Modelo_Chapa': 'TOTAL GERAL',
                'Largura_m': f"{total_area_m2_estoque:.2f}", # Formata para string na exibição
                'Comprimento_m': 'm² (Área Total)', 
                'Tipo_Papel': '', 'Gramatura': '', 'Quantidade_Folhas': '', 'Preco_Kg': '',
                'Peso_Total_kg': total_peso_estoque_kg,
                'Valor_Total_R$': total_valor_estoque_rs
            }
            
            st.dataframe(df_estoque_display, use_container_width=True, 
                         column_config={
                             "Preco_Kg": st.column_config.NumberColumn(format="%.2f"),
                             "Peso_Total_kg": st.column_config.NumberColumn(format="%.2f"),
                             "Valor_Total_R$": st.column_config.NumberColumn(format="%.2f")
                         })
        else:
            st.info("Nenhum item no estoque na memória. Adicione acima ou carregue um arquivo CSV.")

    with st.form("form_pedido"): # O formulário deve englobar toda a lógica do pedido
        st.header("📝 Lançar Pedido e Processar")
        col1, col2, col3 = st.columns(3)
        with col1:
            os_pedido = st.text_input("Ordem de Serviço (OS)", key="pedido_os_input").strip()
            cliente = st.text_input("Cliente", key="pedido_cliente_input").strip()
            descricao = st.text_input("Descrição do Pedido", key="pedido_descricao_input").strip()
        with col2:
            valor_pedido_total = st.number_input("Valor Total do Pedido (R$)", min_value=0.0, format="%.2f", key="pedido_valor_input")
            dim_largura_corte_m = st.number_input("Dimensão Chapa de Corte - Largura (m)", min_value=0.001, format="%.3f", key="pedido_dim_largura_input")
            dim_comprimento_corte_m = st.number_input("Dimensão Chapa de Corte - Comprimento (m)", min_value=0.001, format="%.3f", key="pedido_dim_comprimento_input")
        with col3:
            qtd_caixas = st.number_input("Quantidade de Caixas no Pedido", min_value=1, key="pedido_qtd_caixas_input")
            # Campos para identificar a chapa no estoque
            modelo_chapa_pedido = st.text_input("Modelo da Chapa (do Estoque) para o Pedido", key="pedido_modelo_chapa_input").strip()
            tipo_papel_pedido = st.text_input("Tipo de Papel (do Estoque) para o Pedido", key="pedido_tipo_input").strip()
            gramatura_pedido = st.number_input("Gramatura (do Estoque) para o Pedido (g/m²)", min_value=1, key="pedido_gramatura_input")

        processar_pedido_btn = st.form_submit_button("Processar Pedido")

        if processar_pedido_btn:
            if not os_pedido or not cliente or not descricao or valor_pedido_total <= 0 or \
               dim_largura_corte_m <= 0 or dim_comprimento_corte_m <= 0 or qtd_caixas <= 0 or \
               not modelo_chapa_pedido or not tipo_papel_pedido or gramatura_pedido <= 0:
                st.error("Por favor, preencha todos os campos obrigatórios do pedido corretamente.")
            else:
                # --- Localizar a Chapa no Estoque pela Modelo, Tipo e Gramatura ---
                chapa_estoque_idx = st.session_state.df_estoque[
                    (st.session_state.df_estoque['Modelo_Chapa'] == modelo_chapa_pedido) &
                    (st.session_state.df_estoque['Tipo_Papel'] == tipo_papel_pedido) &
                    (st.session_state.df_estoque['Gramatura'] == gramatura_pedido)
                ].index

                if chapa_estoque_idx.empty:
                    st.error(f"Erro: Chapa do modelo '{modelo_chapa_pedido}' com Tipo '{tipo_papel_pedido}' e Gramatura '{gramatura_pedido}g/m²' não encontrada no estoque. Verifique os dados na aba 'Lançar Estoque'.")
                else:
                    # Obter dados da chapa do estoque
                    chapa_estoque_data = st.session_state.df_estoque.loc[chapa_estoque_idx].iloc[0]
                    largura_chapa_estoque_m = chapa_estoque_data['Largura_m']
                    comprimento_chapa_estoque_m = chapa_estoque_data['Comprimento_m']
                    preco_kg_chapa_estoque = chapa_estoque_data['Preco_Kg']
                    
                    # --- Cálculos do Pedido ---
                    # CONVERTER DIMENSÕES PARA MM para a função de aproveitamento
                    largura_chapa_estoque_mm = largura_chapa_estoque_m * 1000
                    comprimento_chapa_estoque_mm = comprimento_chapa_estoque_m * 1000
                    dim_largura_corte_mm = dim_largura_corte_m * 1000
                    dim_comprimento_corte_mm = dim_comprimento_corte_m * 1000

                    # AGORA A FUNÇÃO 'calcular_aproveitamento_e_retalhos_novo' RECEBE A CHAPA DO ESTOQUE COMO BASE
                    qtd_caixas_por_chapa_base, retalhos_gerados_map = \
                        calcular_aproveitamento_e_retalhos_novo(dim_largura_corte_mm, dim_comprimento_corte_mm, 
                                                           largura_chapa_estoque_mm, comprimento_chapa_estoque_mm)

                    if qtd_caixas_por_chapa_base == 0:
                        st.error(f"Erro: A chapa de corte {dim_largura_corte_m}x{dim_comprimento_corte_m}m não cabe na chapa do estoque '{modelo_chapa_pedido}' ({largura_chapa_estoque_m}x{comprimento_chapa_estoque_m}m) em nenhuma orientação. Verifique as dimensões.")
                    else:
                        num_folhas_consumidas = math.ceil(qtd_caixas / qtd_caixas_por_chapa_base)

                        # --- Verificar e Abater Quantidade no Estoque ---
                        estoque_atual_chapa_qty = st.session_state.df_estoque.loc[chapa_estoque_idx, 'Quantidade_Folhas'].iloc[0]
                        if estoque_atual_chapa_qty < num_folhas_consumidas:
                            st.warning(f"Aviso: Estoque insuficiente do modelo '{modelo_chapa_pedido}' ({tipo_papel_pedido}, {gramatura_pedido}g/m²). Necessário: {num_folhas_consumidas}, Disponível: {estoque_atual_chapa_qty}. O estoque será abatido, mas pode ficar negativo.")
                        
                        st.session_state.df_estoque.loc[chapa_estoque_idx, 'Quantidade_Folhas'] -= num_folhas_consumidas
                        
                        # Atualiza Peso_Total_kg e Valor_Total_R$ para o item abatido
                        existing_qty = st.session_state.df_estoque.loc[chapa_estoque_idx, 'Quantidade_Folhas'].iloc[0]
                        area_chapa_estoque_m2_recalc = largura_chapa_estoque_m * comprimento_chapa_estoque_m
                        peso_m2_kg_chapa_estoque_recalc = gramatura_pedido / 1000 
                        st.session_state.df_estoque.loc[chapa_estoque_idx, 'Peso_Total_kg'] = area_chapa_estoque_m2_recalc * peso_m2_kg_chapa_estoque_recalc * existing_qty
                        st.session_state.df_estoque.loc[chapa_estoque_idx, 'Valor_Total_R$'] = st.session_state.df_estoque.loc[chapa_estoque_idx, 'Peso_Total_kg'] * preco_kg_chapa_estoque


                        # --- Cálculo do Peso Total do Pedido (relacionado ao produto final, não ao consumo da chapa) ---
                        area_chapa_corte_por_caixa_m2 = dim_largura_corte_m * dim_comprimento_corte_m
                        peso_total_pedido_kg = area_chapa_corte_por_caixa_m2 * (gramatura_pedido / 1000) * qtd_caixas

                        # --- Adicionar Retalhos Gerados ao Estoque ---
                        retalhos_gerados_dims_string = [] 

                        for dim_retalho_mm_str, qty_retalho_per_chapa in retalhos_gerados_map.items():
                            qty_total_retalho = qty_retalho_per_chapa * num_folhas_consumidas 
                            if qty_total_retalho == 0:
                                continue
                            
                            retalho_largura_m, retalho_comprimento_m = [float(x)/1000 for x in dim_retalho_mm_str.split('x')]
                            
                            # Procura por retalhos existentes no estoque pelo TIPO, GRAMATURA e DIMENSÃO
                            item_retalho_idx = st.session_state.df_estoque[
                                (st.session_state.df_estoque['Tipo_Papel'] == tipo_papel_pedido) &
                                (st.session_state.df_estoque['Gramatura'] == gramatura_pedido) &
                                (st.session_state.df_estoque['Largura_m'] == retalho_largura_m) &
                                (st.session_state.df_estoque['Comprimento_m'] == retalho_comprimento_m)
                            ].index
                            
                            if not item_retalho_idx.empty:
                                st.session_state.df_estoque.loc[item_retalho_idx, 'Quantidade_Folhas'] += qty_total_retalho
                                # Recalcula peso/valor do retalho atualizado
                                existing_qty_retalho = st.session_state.df_estoque.loc[item_retalho_idx, 'Quantidade_Folhas'].iloc[0]
                                area_retalho_m2_recalc = retalho_largura_m * retalho_comprimento_m
                                preco_kg_retalho = st.session_state.df_estoque.loc[item_retalho_idx, 'Preco_Kg'].iloc[0] 
                                st.session_state.df_estoque.loc[item_retalho_idx, 'Peso_Total_kg'] = area_retalho_m2_recalc * (gramatura_pedido/1000) * existing_qty_retalho
                                st.session_state.df_estoque.loc[item_retalho_idx, 'Valor_Total_R$'] = st.session_state.df_estoque.loc[item_retalho_idx, 'Peso_Total_kg'] * preco_kg_retalho
                            else:
                                # Se o retalho não existe no estoque com essas características, adiciona como novo item
                                st.warning(f"Retalho {dim_retalho_mm_str} ({tipo_papel_pedido}, {gramatura_pedido}g/m²) gerado e adicionado como novo item de estoque com modelo 'RETALHO-{dim_retalho_mm_str}' e Preço/Kg de 0.01. Considere adicioná-lo ou atualizar seu preço na aba 'Lançar Estoque'.")
                                novo_retalho = pd.DataFrame([{
                                    'Modelo_Chapa': f"RETALHO-{dim_retalho_mm_str}", 
                                    'Largura_m': retalho_largura_m,
                                    'Comprimento_m': retalho_comprimento_m,
                                    'Tipo_Papel': tipo_papel_pedido,
                                    'Gramatura': gramatura_pedido,
                                    'Quantidade_Folhas': qty_total_retalho,
                                    'Preco_Kg': 0.01, 
                                    'Peso_Total_kg': retalho_largura_m * retalho_comprimento_m * (gramatura_pedido/1000) * qty_total_retalho,
                                    'Valor_Total_R$': retalho_largura_m * retalho_comprimento_m * (gramatura_pedido/1000) * qty_total_retalho * 0.01
                                }])
                                st.session_state.df_estoque = pd.concat([st.session_state.df_estoque, novo_retalho], ignore_index=True)
                                
                            retalhos_gerados_dims_string.append(f"{qty_total_retalho}x {dim_retalho_mm_str}") 
                        
                        st.session_state.df_estoque = st.session_state.df_estoque.sort_values(by=['Modelo_Chapa', 'Tipo_Papel', 'Gramatura']).reset_index(drop=True)

                        # --- Registrar Pedido no Log da Sessão (st.session_state.df_pedidos) ---
                        novo_pedido_log = pd.DataFrame([{
                            'OS': os_pedido,
                            'Cliente': cliente,
                            'Descricao_Pedido': descricao,
                            'Valor_Pedido_Total_R$': valor_pedido_total, 
                            'Dimensao_Corte_LxC_m': f"{dim_largura_corte_m}x{dim_comprimento_corte_m}",
                            'Quantidade_Caixas': qtd_caixas,
                            'Modelo_Chapa_Pedido': modelo_chapa_pedido,
                            'Tipo_Papel_Pedido': tipo_papel_pedido,
                            'Gramatura_Pedido': gramatura_pedido,
                            'Chapas_Consumidas': num_folhas_consumidas,
                            'Retalhos_Gerados_Dimensoes': ", ".join(retalhos_gerados_dims_string),
                            'Peso_Total_Pedido_kg': peso_total_pedido_kg,
                            'Data_Processamento': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }])
                        st.session_state.df_pedidos = pd.concat([st.session_state.df_pedidos, novo_pedido_log], ignore_index=True)

                        st.success(f"Pedido OS: {os_pedido} processado e estoque atualizado na memória!")
                        st.info(f"O aproveitamento da chapa de corte {dim_largura_corte_m}x{dim_comprimento_corte_m}m na chapa do estoque '{modelo_chapa_pedido}' ({largura_chapa_estoque_m}x{comprimento_chapa_estoque_m}m) é de **{qtd_caixas_por_chapa_base} caixas por folha.**")
                        st.write(f"Você precisará de **{num_folhas_consumidas}** chapas do modelo '{modelo_chapa_pedido}' ({tipo_papel_pedido}, {gramatura_pedido}g/m²).")
                        st.write(f"Serão gerados: {', '.join(retalhos_gerados_dims_string)}. **Importante:** Se quiser controlar e valorizar seus retalhos, adicione-os na aba 'Lançar Estoque' com seus próprios 'Modelo da Chapa' e 'Preço por Kg'.")
                        
                        # Definir flag para indicar que o formulário foi processado com sucesso
                        st.session_state.form_processed_successfully = True

    # --- Fora do st.form(), verificar a flag para fazer o rerun ---
    if 'form_processed_successfully' in st.session_state and st.session_state.form_processed_successfully:
        st.session_state.form_processed_successfully = False # Resetar a flag
        st.rerun() # Recarregar o app para limpar o formulário e atualizar as tabelas

    st.subheader("Últimos Pedidos Processados NESTA Sessão:")
    if not st.session_state.df_pedidos.empty:
        # Reordenar colunas para exibição na tela
        colunas_pedidos_display = [
            'OS', 'Cliente', 'Descricao_Pedido', 'Valor_Pedido_Total_R$', 
            'Peso_Total_Pedido_kg', 'Quantidade_Caixas',
            'Dimensao_Corte_LxC_m', 'Modelo_Chapa_Pedido', 'Tipo_Papel_Pedido', 
            'Gramatura_Pedido', 'Chapas_Consumidas', 'Retalhos_Gerados_Dimensoes', 
            'Data_Processamento'
        ]
        
        st.dataframe(st.session_state.df_pedidos[colunas_pedidos_display].tail(5), use_container_width=True,
                     column_config={
                         "Valor_Pedido_Total_R$": st.column_config.NumberColumn(format="%.2f"),
                         "Peso_Total_Pedido_kg": st.column_config.NumberColumn(format="%.2f")
                     })
    else:
        st.info("Nenhum pedido processado nesta sessão ainda.")

    with tab_relatorios:
        st.header("📊 Relatórios e Downloads")
        st.write("Baixe suas planilhas para salvar os dados permanentemente no seu computador. Lembre-se de fazer o upload do estoque na próxima sessão.")

        st.subheader("Estoque Atual na Memória:")
        if not st.session_state.df_estoque.empty:
            # Calcular totais para exibição na tabela
            total_area_m2_estoque = (st.session_state.df_estoque['Largura_m'] * st.session_state.df_estoque['Comprimento_m'] * st.session_state.df_estoque['Quantidade_Folhas']).sum()
            total_peso_estoque_kg = st.session_state.df_estoque['Peso_Total_kg'].sum()
            total_valor_estoque_rs = st.session_state.df_estoque['Valor_Total_R$'].sum()

            # Criar cópia para exibição na tela e adicionar linha de totais
            df_estoque_display = st.session_state.df_estoque.copy()
            df_estoque_display.loc[''] = '' # Linha em branco para separar
            df_estoque_display.loc['Total Geral'] = {
                'Modelo_Chapa': 'TOTAL GERAL',
                'Largura_m': f"{total_area_m2_estoque:.2f}", # Formata para string na exibição
                'Comprimento_m': 'm² (Área Total)', 
                'Tipo_Papel': '', 'Gramatura': '', 'Quantidade_Folhas': '', 'Preco_Kg': '',
                'Peso_Total_kg': total_peso_estoque_kg,
                'Valor_Total_R$': total_valor_estoque_rs
            }
            
            st.dataframe(df_estoque_display, use_container_width=True, 
                         column_config={
                             "Preco_Kg": st.column_config.NumberColumn(format="%.2f"),
                             "Peso_Total_kg": st.column_config.NumberColumn(format="%.2f"),
                             "Valor_Total_R$": st.column_config.NumberColumn(format="%.2f")
                         })
        else:
            st.info("Nenhum item no estoque na memória. Adicione acima ou carregue um arquivo CSV.")

        st.subheader("Histórico de Pedidos Processados NESTA Sessão:")
        if not st.session_state.df_pedidos.empty:
            # Reordenar colunas para o download
            colunas_pedidos_download = [
                'OS', 'Cliente', 'Descricao_Pedido', 'Valor_Pedido_Total_R$', 
                'Peso_Total_Pedido_kg', 'Quantidade_Caixas',
                'Dimensao_Corte_LxC_m', 'Modelo_Chapa_Pedido', 'Tipo_Papel_Pedido', 
                'Gramatura_Pedido', 'Chapas_Consumidas', 'Retalhos_Gerados_Dimensoes', 
                'Data_Processamento'
            ]
            
            csv_pedidos = st.session_state.df_pedidos[colunas_pedidos_download].to_csv(index=False, sep=';', decimal=',').encode('utf-8')
            st.download_button(
                label="Baixar Histórico de Pedidos (CSV)",
                data=csv_pedidos,
                file_name="pedidos_gbs_historico.csv",
                mime="text/csv",
            )
        else:
            st.info("Nenhum pedido no histórico para download.")


if __name__ == "__main__":
    main()
