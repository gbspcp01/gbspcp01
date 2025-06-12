import streamlit as st
import pandas as pd
import math
import io 
from datetime import datetime

# --- Configurações da Chapa Padrão (Fixas - Apenas para aproveitamento na chapa padrão) ---
# Embora o app trabalhe com qualquer chapa no estoque, esta é a dimensão de referência para calcular retalhos se a chapa cortada for desta base.
LARGURA_CHAPA_PADRAO_MM = 1680  # mm
COMPRIMENTO_CHAPA_PADRAO_MM = 2600  # mm

# --- Lógica de Cálculo Automático de Caixas por Chapa Padrão e Retalhos ---
# Esta função calcula o aproveitamento de uma 'chapa de corte' dentro de uma 'chapa base' (neste caso, a padrão 1680x2600mm)
def calcular_aproveitamento_e_retalhos(largura_corte_mm, comprimento_corte_mm):
    lp = LARGURA_CHAPA_PADRAO_MM
    cp = COMPRIMENTO_CHAPA_PADRAO_MM

    # Orientação 1: Cortar largura_corte_mm na largura da chapa padrão (lp) e comprimento_corte_mm no comprimento (cp)
    num_pecas_largura_1 = math.floor(lp / largura_corte_mm)
    num_pecas_comprimento_1 = math.floor(cp / comprimento_corte_mm)
    qtd_caixas_orientacao_1 = num_pecas_largura_1 * num_pecas_comprimento_1

    sobra_largura_1 = lp - (num_pecas_largura_1 * largura_corte_mm)
    sobra_comprimento_1 = cp - (num_pecas_comprimento_1 * comprimento_corte_mm)
    retalho_1_orientacao_1 = f"{sobra_largura_1}x{cp}" # Sobra na largura, percorrendo todo o comprimento
    retalho_2_orientacao_1 = f"{lp}x{sobra_comprimento_1}" # Sobra no comprimento, percorrendo toda a largura

    # Orientação 2: Cortar comprimento_corte_mm na largura da chapa padrão (lp) e largura_corte_mm no comprimento (cp)
    num_pecas_largura_2 = math.floor(lp / comprimento_corte_mm)
    num_pecas_comprimento_2 = math.floor(cp / largura_corte_mm)
    qtd_caixas_orientacao_2 = num_pecas_largura_2 * num_pecas_comprimento_2
    
    sobra_largura_2 = lp - (num_pecas_largura_2 * comprimento_corte_mm)
    sobra_comprimento_2 = cp - (num_pecas_comprimento_2 * largura_corte_mm)
    retalho_1_orientacao_2 = f"{sobra_largura_2}x{cp}"
    retalho_2_orientacao_2 = f"{lp}x{sobra_comprimento_2}"

    # Escolher a melhor orientação (maior número de caixas)
    if qtd_caixas_orientacao_1 >= qtd_caixas_orientacao_2:
        return qtd_caixas_orientacao_1, retalho_1_orientacao_1, retalho_2_orientacao_1
    else:
        return qtd_caixas_orientacao_2, retalho_1_orientacao_2, retalho_2_orientacao_2

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
                st.session_state.df_estoque = pd.read_csv(uploaded_file, sep=';', decimal=',') # Adicionado decimal=',' para números com vírgula
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
                        st.success(f"Modelo '{modelo_chapa}' adicionado ao estoque!")
                    
                    st.session_state.df_estoque = st.session_state.df_estoque.sort_values(by=['Modelo_Chapa', 'Tipo_Papel', 'Gramatura']).reset_index(drop=True)


        st.subheader("Estoque Atual na Memória:")
        if not st.session_state.df_estoque.empty:
            st.dataframe(st.session_state.df_estoque, use_container_width=True, 
                         column_config={
                             "Preco_Kg": st.column_config.NumberColumn(format="%.2f"),
                             "Peso_Total_kg": st.column_config.NumberColumn(format="%.2f"),
                             "Valor_Total_R$": st.column_config.NumberColumn(format="%.2f")
                         })
        else:
            st.info("Nenhum item no estoque na memória. Adicione acima ou carregue um arquivo CSV.")

    with tab_pedido:
        st.header("📝 Lançar Pedido e Processar")
        with st.form("form_pedido"):
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
                        peso_m2_kg_estoque = chapa_estoque_data['Gramatura'] / 1000 # Convertendo g/m2 para kg/m2
                        
                        # --- Cálculos do Pedido ---
                        # Converter dimensões de corte de M para MM para a função de aproveitamento
                        dim_largura_corte_mm = dim_largura_corte_m * 1000
                        dim_comprimento_corte_mm = dim_comprimento_corte_m * 1000

                        # A função calcular_aproveitamento_e_retalhos ainda usa a CHAPA PADRÃO FIXA (1680x2600mm)
                        # Se o aproveitamento deveria ser da chapa ESCOLHIDA no estoque, essa função precisaria ser mais dinâmica.
                        # Por enquanto, ela calcula o aproveitamento na chapa padrão de 1680x2600mm.
                        # Se você quiser que ela use a dimensão da chapa do estoque (largura_chapa_estoque_m x comprimento_chapa_estoque_m), precisamos ajustar a função.
                        
                        # UTILIZANDO A LÓGICA ATUAL DE APROVEITAMENTO NA CHAPA PADRÃO FIXA (1680x2600mm)
                        qtd_caixas_por_chapa_padrao, retalho1_dim_mm, retalho2_dim_mm = \
                            calcular_aproveitamento_e_retalhos(dim_largura_corte_mm, dim_comprimento_corte_mm)

                        if qtd_caixas_por_chapa_padrao == 0:
                            st.error(f"Erro: A chapa de corte {dim_largura_corte_m}x{dim_comprimento_corte_m}m não cabe na chapa padrão {LARGURA_CHAPA_PADRAO_MM}x{COMPRIMENTO_CHAPA_PADRAO_MM}mm em nenhuma orientação. Verifique as dimensões.")
                        else:
                            num_folhas_consumidas = math.ceil(qtd_caixas / qtd_caixas_por_chapa_padrao)

                            # --- Verificar e Abater Quantidade no Estoque ---
                            estoque_atual_chapa_qty = st.session_state.df_estoque.loc[chapa_estoque_idx, 'Quantidade_Folhas'].iloc[0]
                            if estoque_atual_chapa_qty < num_folhas_consumidas:
                                st.warning(f"Aviso: Estoque insuficiente do modelo '{modelo_chapa_pedido}' ({tipo_papel_pedido}, {gramatura_pedido}g/m²). Necessário: {num_folhas_consumidas}, Disponível: {estoque_atual_chapa_qty}. O estoque será abatido, mas pode ficar negativo.")
                            
                            st.session_state.df_estoque.loc[chapa_estoque_idx, 'Quantidade_Folhas'] -= num_folhas_consumidas
                            
                            # Atualiza Peso_Total_kg e Valor_Total_R$ para o item abatido
                            existing_qty = st.session_state.df_estoque.loc[chapa_estoque_idx, 'Quantidade_Folhas'].iloc[0]
                            area_chapa_estoque_m2 = largura_chapa_estoque_m * comprimento_chapa_estoque_m
                            peso_m2_kg_chapa_estoque = gramatura_pedido / 1000 # Pega a gramatura do pedido/chapa do estoque
                            st.session_state.df_estoque.loc[chapa_estoque_idx, 'Peso_Total_kg'] = area_chapa_estoque_m2 * peso_m2_kg_chapa_estoque * existing_qty
                            st.session_state.df_estoque.loc[chapa_estoque_idx, 'Valor_Total_R$'] = st.session_state.df_estoque.loc[chapa_estoque_idx, 'Peso_Total_kg'] * preco_kg_chapa_estoque


                            # --- Cálculo do Peso Total do Pedido ---
                            area_chapa_corte_por_caixa_m2 = dim_largura_corte_m * dim_comprimento_corte_m
                            peso_total_pedido_kg = area_chapa_corte_por_caixa_m2 * (gramatura_pedido / 1000) * qtd_caixas

                            # --- Adicionar Retalhos Gerados ao Estoque ---
                            retalhos_gerados_info = {} 
                            
                            # Retalhos são gerados da chapa PADRÃO (1680x2600mm), não da chapa ESCOLHIDA no estoque
                            # Isso significa que as dimensões dos retalhos (1680x1240, 384x1360) são fixas.
                            # Para que a lógica de retalhos funcione, o modelo 'Modelo_Chapa' para esses retalhos também precisa ser adicionado no estoque.
                            # Para simplificar aqui, vamos apenas somar nas quantidades existentes.
                            
                            # Retalho 1
                            if retalho1_dim_mm != "0x2600" and retalho1_dim_mm != "1680x0": 
                                dim_retalho_str = retalho1_dim_mm # Mantém como string "LarguraXComprimento"
                                retalhos_gerados_info[dim_retalho_str] = retalhos_gerados_info.get(dim_retalho_str, 0) + num_folhas_consumidas
                            
                            # Retalho 2
                            if retalho2_dim_mm != "0x2600" and retalho2_dim_mm != "1680x0": 
                                dim_retalho_str = retalho2_dim_mm
                                retalhos_gerados_info[dim_retalho_str] = retalhos_gerados_info.get(dim_retalho_str, 0) + num_folhas_consumidas
                            
                            for dim_retalho_mm_str, qty_retalho in retalhos_gerados_info.items():
                                # É crucial que o 'Modelo_Chapa' dos retalhos seja consistente se você os gerencia assim.
                                # Por simplicidade aqui, vamos procurar por retalhos SEM MODELO_CHAPA ou com modelo genérico.
                                # Se você tem modelos específicos para retalhos, essa parte precisa ser ajustada.
                                
                                # Convertendo dimensão do retalho de MM para M para procurar no estoque
                                retalho_largura_m, retalho_comprimento_m = [float(x)/1000 for x in dim_retalho_mm_str.split('x')]
                                
                                item_retalho_idx = st.session_state.df_estoque[
                                    (st.session_state.df_estoque['Largura_m'] == retalho_largura_m) &
                                    (st.session_state.df_estoque['Comprimento_m'] == retalho_comprimento_m) &
                                    (st.session_state.df_estoque['Tipo_Papel'] == tipo_papel_pedido) &
                                    (st.session_state.df_estoque['Gramatura'] == gramatura_pedido)
                                ].index
                                if not item_retalho_idx.empty:
                                    st.session_state.df_estoque.loc[item_retalho_idx, 'Quantidade_Folhas'] += qty_retalho
                                    # Recalcula peso/valor do retalho atualizado
                                    existing_qty_retalho = st.session_state.df_estoque.loc[item_retalho_idx, 'Quantidade_Folhas'].iloc[0]
                                    area_retalho_m2 = retalho_largura_m * retalho_comprimento_m
                                    preco_kg_retalho = st.session_state.df_estoque.loc[item_retalho_idx, 'Preco_Kg'].iloc[0] # Usa o preço do retalho se já existir
                                    st.session_state.df_estoque.loc[item_retalho_idx, 'Peso_Total_kg'] = area_retalho_m2 * (gramatura_pedido/1000) * existing_qty_retalho
                                    st.session_state.df_estoque.loc[item_retalho_idx, 'Valor_Total_R$'] = st.session_state.df_estoque.loc[item_retalho_idx, 'Peso_Total_kg'] * preco_kg_retalho
                                else:
                                    # Se o retalho não existe com esse Modelo_Chapa (que não foi especificado), cria um item genérico de retalho
                                    # MODELO_CHAPA para retalhos precisa ser genérico ou especificado pelo usuário ao adicionar.
                                    # Aqui, um modelo genérico 'Retalho_<dimensão>' é usado.
                                    st.warning(f"Retalho {dim_retalho_str} ({tipo_papel_pedido}, {gramatura_pedido}g/m²) gerado e adicionado como novo item de estoque. Você deve adicionar este 'Modelo_Chapa' para retalhos com um preço por Kg se quiser seu valor calculado.")
                                    novo_retalho = pd.DataFrame([{
                                        'Modelo_Chapa': f"Retalho {dim_retalho_str}", # Nome genérico para retalho
                                        'Largura_m': retalho_largura_m,
                                        'Comprimento_m': retalho_comprimento_m,
                                        'Tipo_Papel': tipo_papel_pedido,
                                        'Gramatura': gramatura_pedido,
                                        'Quantidade_Folhas': qty_retalho,
                                        'Preco_Kg': 0.01, # Preço padrão baixo para retalho novo, ou ajustável
                                        'Peso_Total_kg': area_retalho_m2 * (gramatura_pedido/1000) * qty_retalho,
                                        'Valor_Total_R$': area_retalho_m2 * (gramatura_pedido/1000) * qty_retalho * 0.01
                                    }])
                                    st.session_state.df_estoque = pd.concat([st.session_state.df_estoque, novo_retalho], ignore_index=True)
                            
                            st.session_state.df_estoque = st.session_state.df_estoque.sort_values(by=['Modelo_Chapa', 'Tipo_Papel', 'Gramatura']).reset_index(drop=True)

                            # --- Registrar Pedido no Log da Sessão (st.session_state.df_pedidos) ---
                            novo_pedido_log = pd.DataFrame([{
                                'OS': os_pedido,
                                'Cliente': cliente,
                                'Descricao_Pedido': descricao,
                                'Valor_Pedido_Total_R$': valor_pedido_total, # Este é o valor total do pedido inserido
                                'Dimensao_Corte_LxC_m': f"{dim_largura_corte_m}x{dim_comprimento_corte_m}",
                                'Quantidade_Caixas': qtd_caixas,
                                'Modelo_Chapa_Pedido': modelo_chapa_pedido,
                                'Tipo_Papel_Pedido': tipo_papel_pedido,
                                'Gramatura_Pedido': gramatura_pedido,
                                'Chapas_Consumidas': num_folhas_consumidas,
                                'Retalhos_Gerados_Dimensoes': str(list(retalhos_gerados_info.keys())),
                                'Retalhos_1680x1240_Gerados': retalhos_gerados_info.get("1680x1240", 0),
                                'Retalhos_384x1360_Gerados': retalhos_gerados_info.get("384x1360", 0),
                                'Peso_Total_Pedido_kg': peso_total_pedido_kg,
                                'Data_Processamento': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }])
                            st.session_state.df_pedidos = pd.concat([st.session_state.df_pedidos, novo_pedido_log], ignore_index=True)

                            st.success(f"Pedido OS: {os_pedido} processado e estoque atualizado na memória!")
                            st.info(f"O aproveitamento da chapa de corte {dim_largura_corte_m}x{dim_comprimento_corte_m}m na chapa padrão {LARGURA_CHAPA_PADRAO_MM}x{COMPRIMENTO_CHAPA_PADRAO_MM}mm é de **{qtd_caixas_por_chapa_padrao} caixas por chapa padrão.**")
                            st.write(f"Você precisará de **{num_folhas_consumidas}** chapas do modelo '{modelo_chapa_pedido}' ({tipo_papel_pedido}, {gramatura_pedido}g/m²).")
                            st.write(f"Serão gerados: {retalhos_gerados_info}. Verifique se adicionou os modelos de retalho ao estoque para ter seus valores calculados corretamente.")
                            
                            # Limpar campos do formulário de pedido
                            st.session_state.pedido_os_input = ''
                            st.session_state.pedido_cliente_input = ''
                            st.session_state.pedido_descricao_input = ''
                            st.session_state.pedido_valor_input = 0.0
                            st.session_state.pedido_dim_largura_input = 0.0
                            st.session_state.pedido_dim_comprimento_input = 0.0
                            st.session_state.pedido_qtd_caixas_input = 0
                            st.session_state.pedido_modelo_chapa_input = ''
                            st.session_state.pedido_tipo_input = ''
                            st.session_state.pedido_gramatura_input = 0


        st.subheader("Últimos Pedidos Processados NESTA Sessão:")
        if not st.session_state.df_pedidos.empty:
            st.dataframe(st.session_state.df_pedidos.tail(5), use_container_width=True,
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
            # Calcular totais do estoque para exibir
            total_peso_estoque_kg = st.session_state.df_estoque['Peso_Total_kg'].sum()
            total_valor_estoque_rs = st.session_state.df_estoque['Valor_Total_R$'].sum()
            
            st.metric(label="**Peso Total do Estoque**", value=f"{total_peso_estoque_kg/1000:.2f} Toneladas")
            st.metric(label="**Valor Total do Estoque**", value=f"R$ {total_valor_estoque_rs:.2f}")

            st.dataframe(st.session_state.df_estoque, use_container_width=True,
                         column_config={
                             "Preco_Kg": st.column_config.NumberColumn(format="%.2f"),
                             "Peso_Total_kg": st.column_config.NumberColumn(format="%.2f"),
                             "Valor_Total_R$": st.column_config.NumberColumn(format="%.2f")
                         })
            
            # --- Botão de Download do Estoque em CSV ---
            csv_estoque = st.session_state.df_estoque.to_csv(index=False, sep=';', decimal=',').encode('utf-8') 
            st.download_button(
                label="Baixar Estoque Atualizado (CSV)",
                data=csv_estoque,
                file_name="estoque_gbs_atualizado.csv",
                mime="text/csv",
            )
        else:
            st.info("Estoque vazio para download.")

        st.subheader("Histórico de Pedidos Processados NESTA Sessão:")
        if not st.session_state.df_pedidos.empty:
            st.dataframe(st.session_state.df_pedidos, use_container_width=True,
                         column_config={
                             "Valor_Pedido_Total_R$": st.column_config.NumberColumn(format="%.2f"),
                             "Peso_Total_Pedido_kg": st.column_config.NumberColumn(format="%.2f")
                         })
            
            # --- Botão de Download do Histórico de Pedidos em CSV ---
            csv_pedidos = st.session_state.df_pedidos.to_csv(index=False, sep=';', decimal=',').encode('utf-8')
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
     


    
  

       
       
                 
                      
                               
                      
                      
             
          


