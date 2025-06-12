import streamlit as st
import pandas as pd
import math
import os
from datetime import datetime

# --- Configurações da Chapa Padrão (Fixas) ---
LARGURA_CHAPA_PADRAO = 1680  # mm
COMPRIMENTO_CHAPA_PADRAO = 2600  # mm

# --- Nomes dos Arquivos e Abas ---
ARQUIVO_ESTOQUE = 'estoque_gbs.xlsx'
ABA_ESTOQUE = 'Estoque_Atual'
ARQUIVO_PEDIDOS = 'pedidos_gbs.xlsx'
ABA_PEDIDOS = 'Pedidos_Processados'

# --- Função para Inicializar ou Carregar o Estoque ---
def carregar_estoque():
    if not os.path.exists(ARQUIVO_ESTOQUE):
        # Se o arquivo não existe, cria um DataFrame vazio com as colunas
        df_estoque = pd.DataFrame(columns=[
            'Dimensao_Chapa', 'Tipo_Papelao', 'Gramatura', 'Quantidade_Folhas', 'Peso_m2_kg'
        ])
        # Salva o DataFrame vazio para criar o arquivo e a aba
        with pd.ExcelWriter(ARQUIVO_ESTOQUE, engine='openpyxl') as writer:
            df_estoque.to_excel(writer, sheet_name=ABA_ESTOQUE, index=False)
    else:
        # Se o arquivo existe, carrega
        df_estoque = pd.read_excel(ARQUIVO_ESTOQUE, sheet_name=ABA_ESTOQUE)
    return df_estoque

# --- Função para Inicializar ou Carregar o Log de Pedidos ---
def carregar_pedidos():
    if not os.path.exists(ARQUIVO_PEDIDOS):
        # Se o arquivo não existe, cria um DataFrame vazio com as colunas
        df_pedidos = pd.DataFrame(columns=[
            'OS', 'Cliente', 'Descricao_Pedido', 'Valor_Pedido', 'Dimensao_Corte_LxC', 
            'Quantidade_Caixas', 'Tipo_Papelao_Pedido', 'Gramatura_Pedido', 
            'Chapas_Padrao_Necessarias', 'Retalhos_1680x1240_Gerados', 
            'Retalhos_384x1360_Gerados', 'Peso_Total_Pedido_kg', 'Data_Processamento'
        ])
        # Salva o DataFrame vazio para criar o arquivo e a aba
        with pd.ExcelWriter(ARQUIVO_PEDIDOS, engine='openpyxl') as writer:
            df_pedidos.to_excel(writer, sheet_name=ABA_PEDIDOS, index=False)
    else:
        # Se o arquivo existe, carrega
        df_pedidos = pd.read_excel(ARQUIVO_PEDIDOS, sheet_name=ABA_PEDIDOS)
    return df_pedidos

# --- Função para Salvar o Estoque ---
def salvar_estoque(df_estoque):
    with pd.ExcelWriter(ARQUIVO_ESTOQUE, engine='openpyxl') as writer:
        df_estoque.to_excel(writer, sheet_name=ABA_ESTOQUE, index=False)

# --- Função para Salvar o Log de Pedidos ---
def salvar_pedidos(df_pedidos):
    with pd.ExcelWriter(ARQUIVO_PEDIDOS, engine='openpyxl') as writer:
        df_pedidos.to_excel(writer, sheet_name=ABA_PEDIDOS, index=False)

# --- Lógica de Cálculo Automático de Caixas por Chapa Padrão e Retalhos ---
def calcular_aproveitamento_e_retalhos(largura_corte, comprimento_corte):
    # Dimensões da chapa padrão
    lp = LARGURA_CHAPA_PADRAO
    cp = COMPRIMENTO_CHAPA_PADRAO

    # --- Orientação 1: Cortar largura_corte na largura da chapa padrão (lp) e comprimento_corte no comprimento (cp) ---
    num_pecas_largura_1 = math.floor(lp / largura_corte)
    num_pecas_comprimento_1 = math.floor(cp / comprimento_corte)
    qtd_caixas_orientacao_1 = num_pecas_largura_1 * num_pecas_comprimento_1

    # Sobras Orientação 1
    sobra_largura_1 = lp - (num_pecas_largura_1 * largura_corte)
    sobra_comprimento_1 = cp - (num_pecas_comprimento_1 * comprimento_corte)
    retalho_1_orientacao_1 = f"{sobra_largura_1}x{cp}" # Sobra na largura, percorrendo todo o comprimento
    retalho_2_orientacao_1 = f"{lp}x{sobra_comprimento_1}" # Sobra no comprimento, percorrendo toda a largura

    # --- Orientação 2: Cortar comprimento_corte na largura da chapa padrão (lp) e largura_corte no comprimento (cp) ---
    num_pecas_largura_2 = math.floor(lp / comprimento_corte)
    num_pecas_comprimento_2 = math.floor(cp / largura_corte)
    qtd_caixas_orientacao_2 = num_pecas_largura_2 * num_pecas_comprimento_2
    
    # Sobras Orientação 2
    sobra_largura_2 = lp - (num_pecas_largura_2 * comprimento_corte)
    sobra_comprimento_2 = cp - (num_pecas_comprimento_2 * largura_corte)
    retalho_1_orientacao_2 = f"{sobra_largura_2}x{cp}"
    retalho_2_orientacao_2 = f"{lp}x{sobra_comprimento_2}"

    # --- Escolher a melhor orientação (maior número de caixas) ---
    if qtd_caixas_orientacao_1 >= qtd_caixas_orientacao_2:
        return qtd_caixas_orientacao_1, retalho_1_orientacao_1, retalho_2_orientacao_1
    else:
        return qtd_caixas_orientacao_2, retalho_1_orientacao_2, retalho_2_orientacao_2

# --- Função para o Layout do Streamlit ---
def main():
    st.set_page_config(layout="wide", page_title="GBS - Planejamento de Produção")
    st.title("📦 GBS - Planejamento e Controle de Produção")

    # Carregar estoque e pedidos (ou criar se não existirem)
    if 'df_estoque' not in st.session_state:
        st.session_state.df_estoque = carregar_estoque()
    if 'df_pedidos' not in st.session_state:
        st.session_state.df_pedidos = carregar_pedidos()

    # --- Abas do Aplicativo ---
    tab_estoque, tab_pedido, tab_relatorios = st.tabs(["Lançar Estoque", "Lançar Pedido", "Relatórios"])

    with tab_estoque:
        st.header("➕ Lançar e Visualizar Estoque")
        with st.form("form_estoque"):
            col1, col2 = st.columns(2)
            with col1:
                dimensao = st.text_input("Dimensão Chapa (ex: 1680x2600)", key="estoque_dimensao_input").strip()
                tipo_papelao = st.text_input("Tipo de Papelão (ex: Onda C)", key="estoque_tipo_input").strip()
            with col2:
                gramatura = st.number_input("Gramatura (g/m²)", min_value=1, value=370, key="estoque_gramatura_input")
                quantidade = st.number_input("Quantidade de Folhas", min_value=1, value=1000, key="estoque_quantidade_input")
            
            # Campo para Peso_m2_kg: Pode ser calculado ou digitado. Por enquanto, digitado.
            peso_m2_kg = st.number_input("Peso por m² (kg/m² - ex: 0.370 para 370g/m²)", min_value=0.001, value=gramatura/1000, format="%.3f", key="estoque_peso_m2_input")

            adicionar_estoque_btn = st.form_submit_button("Adicionar/Atualizar Item no Estoque")
            
            if adicionar_estoque_btn:
                if not dimensao or not tipo_papelao or gramatura <= 0 or quantidade <= 0 or peso_m2_kg <= 0:
                    st.error("Por favor, preencha todos os campos do estoque corretamente.")
                else:
                    # Verifica se o item já existe (mesma dimensão, tipo, gramatura)
                    item_existente_idx = st.session_state.df_estoque[
                        (st.session_state.df_estoque['Dimensao_Chapa'] == dimensao) &
                        (st.session_state.df_estoque['Tipo_Papelao'] == tipo_papelao) &
                        (st.session_state.df_estoque['Gramatura'] == gramatura)
                    ].index

                    if not item_existente_idx.empty:
                        # Atualiza a quantidade do item existente
                        st.session_state.df_estoque.loc[item_existente_idx, 'Quantidade_Folhas'] += quantidade
                        st.success(f"Quantidade de {dimensao} {tipo_papelao} {gramatura}g/m² atualizada para {st.session_state.df_estoque.loc[item_existente_idx, 'Quantidade_Folhas'].iloc[0]}.")
                    else:
                        # Adiciona novo item
                        novo_item = pd.DataFrame([{
                            'Dimensao_Chapa': dimensao,
                            'Tipo_Papelao': tipo_papelao,
                            'Gramatura': gramatura,
                            'Quantidade_Folhas': quantidade,
                            'Peso_m2_kg': peso_m2_kg
                        }])
                        st.session_state.df_estoque = pd.concat([st.session_state.df_estoque, novo_item], ignore_index=True)
                        st.success(f"Item de estoque {dimensao} adicionado com sucesso!")
                    salvar_estoque(st.session_state.df_estoque) # Salva no arquivo

        st.subheader("Estoque Atual:")
        if not st.session_state.df_estoque.empty:
            st.dataframe(st.session_state.df_estoque, use_container_width=True)
        else:
            st.info("Nenhum item no estoque. Adicione acima.")

    with tab_pedido:
        st.header("📝 Lançar Pedido e Processar")
        with st.form("form_pedido"):
            col1, col2, col3 = st.columns(3)
            with col1:
                os_pedido = st.text_input("Ordem de Serviço (OS)", key="pedido_os_input").strip()
                cliente = st.text_input("Cliente", key="pedido_cliente_input").strip()
                descricao = st.text_input("Descrição do Pedido", key="pedido_descricao_input").strip()
            with col2:
                valor_pedido = st.number_input("Valor do Pedido (R$)", min_value=0.0, format="%.2f", key="pedido_valor_input")
                dim_largura_corte = st.number_input("Dimensão Chapa de Corte - Largura (mm)", min_value=1, key="pedido_dim_largura_input")
                dim_comprimento_corte = st.number_input("Dimensão Chapa de Corte - Comprimento (mm)", min_value=1, key="pedido_dim_comprimento_input")
            with col3:
                qtd_caixas = st.number_input("Quantidade de Caixas no Pedido", min_value=1, key="pedido_qtd_caixas_input")
                tipo_papelao_pedido = st.text_input("Tipo de Papelão do Pedido (ex: Onda C)", key="pedido_tipo_input").strip()
                gramatura_pedido = st.number_input("Gramatura do Pedido (g/m²)", min_value=1, key="pedido_gramatura_input")

            processar_pedido_btn = st.form_submit_button("Processar Pedido")

            if processar_pedido_btn:
                if not os_pedido or not cliente or not descricao or valor_pedido <= 0 or dim_largura_corte <= 0 or dim_comprimento_corte <= 0 or qtd_caixas <= 0 or not tipo_papelao_pedido or gramatura_pedido <= 0:
                    st.error("Por favor, preencha todos os campos do pedido corretamente.")
                else:
                    # --- Verificar disponibilidade no estoque ---
                    # Encontrar a chapa padrão correspondente no estoque (1680x2600 e mesma gramatura/tipo)
                    chapa_padrao_estoque_idx = st.session_state.df_estoque[
                        (st.session_state.df_estoque['Dimensao_Chapa'] == f"{LARGURA_CHAPA_PADRAO}x{COMPRIMENTO_CHAPA_PADRAO}") &
                        (st.session_state.df_estoque['Tipo_Papelao'] == tipo_papelao_pedido) &
                        (st.session_state.df_estoque['Gramatura'] == gramatura_pedido)
                    ].index

                    if chapa_padrao_estoque_idx.empty:
                        st.error(f"Erro: Chapa padrão {LARGURA_CHAPA_PADRAO}x{COMPRIMENTO_CHAPA_PADRAO} com Tipo '{tipo_papelao_pedido}' e Gramatura '{gramatura_pedido}g/m²' não encontrada no estoque. Adicione-a primeiro.")
                    else:
                        # --- Cálculos do Pedido ---
                        qtd_caixas_por_chapa_padrao, retalho1_dim, retalho2_dim = \
                            calcular_aproveitamento_e_retalhos(dim_largura_corte, dim_comprimento_corte)

                        if qtd_caixas_por_chapa_padrao == 0:
                            st.error(f"Erro: A chapa de corte {dim_largura_corte}x{dim_comprimento_corte} não cabe na chapa padrão {LARGURA_CHAPA_PADRAO}x{COMPRIMENTO_CHAPA_PADRAO} em nenhuma orientação. Verifique as dimensões.")
                        else:
                            num_folhas_padrao_necessarias = math.ceil(qtd_caixas / qtd_caixas_por_chapa_padrao)

                            # Verificar se há chapas suficientes no estoque
                            estoque_atual_chapa_padrao = st.session_state.df_estoque.loc[chapa_padrao_estoque_idx, 'Quantidade_Folhas'].iloc[0]
                            if estoque_atual_chapa_padrao < num_folhas_padrao_necessarias:
                                st.warning(f"Aviso: Estoque insuficiente de chapas {LARGURA_CHAPA_PADRAO}x{COMPRIMENTO_CHAPA_PADRAO} ({tipo_papelao_pedido}, {gramatura_pedido}g/m²). Necessário: {num_folhas_padrao_necessarias}, Disponível: {estoque_atual_chapa_padrao}. O estoque será negativo.")
                            
                            # --- Cálculo do Peso ---
                            area_chapa_corte_por_caixa_mm2 = dim_largura_corte * dim_comprimento_corte
                            area_total_necessaria_mm2 = area_chapa_corte_por_caixa_mm2 * qtd_caixas
                            area_total_necessaria_m2 = area_total_necessaria_mm2 / 1_000_000
                            
                            peso_m2_kg_estoque = st.session_state.df_estoque.loc[chapa_padrao_estoque_idx, 'Peso_m2_kg'].iloc[0]
                            peso_total_pedido_kg = area_total_necessaria_m2 * peso_m2_kg_estoque

                            # --- Atualização do Estoque (Abater e Adicionar Retalhos) ---
                            # Abater chapas padrão
                            st.session_state.df_estoque.loc[chapa_padrao_estoque_idx, 'Quantidade_Folhas'] -= num_folhas_padrao_necessarias
                            
                            # Adicionar retalhos gerados
                            # Retalho 1
                            if retalho1_dim != "0x2600" and retalho1_dim != "1680x0": # Ignora retalhos zero
                                item_retalho1_idx = st.session_state.df_estoque[
                                    (st.session_state.df_estoque['Dimensao_Chapa'] == retalho1_dim) &
                                    (st.session_state.df_estoque['Tipo_Papelao'] == tipo_papelao_pedido) &
                                    (st.session_state.df_estoque['Gramatura'] == gramatura_pedido)
                                ].index
                                if not item_retalho1_idx.empty:
                                    st.session_state.df_estoque.loc[item_retalho1_idx, 'Quantidade_Folhas'] += num_folhas_padrao_necessarias
                                else:
                                    novo_retalho1 = pd.DataFrame([{
                                        'Dimensao_Chapa': retalho1_dim,
                                        'Tipo_Papelao': tipo_papelao_pedido,
                                        'Gramatura': gramatura_pedido,
                                        'Quantidade_Folhas': num_folhas_padrao_necessarias,
                                        'Peso_m2_kg': peso_m2_kg_estoque # Assume mesmo peso por m2
                                    }])
                                    st.session_state.df_estoque = pd.concat([st.session_state.df_estoque, novo_retalho1], ignore_index=True)
                            
                            # Retalho 2
                            if retalho2_dim != "0x2600" and retalho2_dim != "1680x0": # Ignora retalhos zero
                                item_retalho2_idx = st.session_state.df_estoque[
                                    (st.session_state.df_estoque['Dimensao_Chapa'] == retalho2_dim) &
                                    (st.session_state.df_estoque['Tipo_Papelao'] == tipo_papelao_pedido) &
                                    (st.session_state.df_estoque['Gramatura'] == gramatura_pedido)
                                ].index
                                if not item_retalho2_idx.empty:
                                    st.session_state.df_estoque.loc[item_retalho2_idx, 'Quantidade_Folhas'] += num_folhas_padrao_necessarias
                                else:
                                    novo_retalho2 = pd.DataFrame([{
                                        'Dimensao_Chapa': retalho2_dim,
                                        'Tipo_Papelao': tipo_papelao_pedido,
                                        'Gramatura': gramatura_pedido,
                                        'Quantidade_Folhas': num_folhas_padrao_necessarias,
                                        'Peso_m2_kg': peso_m2_kg_estoque
                                    }])
                                    st.session_state.df_estoque = pd.concat([st.session_state.df_estoque, novo_retalho2], ignore_index=True)

                            # Salva o estoque atualizado
                            salvar_estoque(st.session_state.df_estoque)

                            # --- Registrar Pedido no Log ---
                            novo_pedido_log = pd.DataFrame([{
                                'OS': os_pedido,
                                'Cliente': cliente,
                                'Descricao_Pedido': descricao,
                                'Valor_Pedido': valor_pedido,
                                'Dimensao_Corte_LxC': f"{dim_largura_corte}x{dim_comprimento_corte}",
                                'Quantidade_Caixas': qtd_caixas,
                                'Tipo_Papelao_Pedido': tipo_papelao_pedido,
                                'Gramatura_Pedido': gramatura_pedido,
                                'Chapas_Padrao_Necessarias': num_folhas_padrao_necessarias,
                                'Retalhos_1680x1240_Gerados': num_folhas_padrao_necessarias if "1680x1240" == retalho1_dim or "1680x1240" == retalho2_dim else 0, # Melhorar isso no futuro
                                'Retalhos_384x1360_Gerados': num_folhas_padrao_necessarias if "384x1360" == retalho1_dim or "384x1360" == retalho2_dim else 0, # Melhorar isso no futuro
                                'Peso_Total_Pedido_kg': peso_total_pedido_kg,
                                'Data_Processamento': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }])
                            st.session_state.df_pedidos = pd.concat([st.session_state.df_pedidos, novo_pedido_log], ignore_index=True)
                            salvar_pedidos(st.session_state.df_pedidos) # Salva no arquivo

                            st.success(f"Pedido OS: {os_pedido} processado e estoque atualizado com sucesso!")
                            st.info(f"O aproveitamento para a chapa de corte {dim_largura_corte}x{dim_comprimento_corte} na chapa padrão {LARGURA_CHAPA_PADRAO}x{COMPRIMENTO_CHAPA_PADRAO} é de **{qtd_caixas_por_chapa_padrao} caixas por chapa padrão.**")
                            st.write(f"Você precisará de **{num_folhas_padrao_necessarias}** chapas padrão de {LARGURA_CHAPA_PADRAO}x{COMPRIMENTO_CHAPA_PADRAO}.")
                            st.write(f"Serão gerados **{num_folhas_padrao_necessarias}** retalhos de **{retalho1_dim}** e **{num_folhas_padrao_necessarias}** retalhos de **{retalho2_dim}** (se não forem dimensões zero).")
                            
                            # Limpar campos do formulário de pedido (após sucesso)
                            st.session_state.pedido_os_input = ''
                            st.session_state.pedido_cliente_input = ''
                            st.session_state.pedido_descricao_input = ''
                            st.session_state.pedido_valor_input = 0.0
                            st.session_state.pedido_dim_largura_input = 0
                            st.session_state.pedido_dim_comprimento_input = 0
                            st.session_state.pedido_qtd_caixas_input = 0
                            st.session_state.pedido_tipo_input = ''
                            st.session_state.pedido_gramatura_input = 0


        st.subheader("Últimos Pedidos Processados:")
        if not st.session_state.df_pedidos.empty:
            st.dataframe(st.session_state.df_pedidos.tail(5), use_container_width=True) # Mostra os 5 últimos
        else:
            st.info("Nenhum pedido processado ainda.")

    with tab_relatorios:
        st.header("📊 Relatórios e Downloads")

        st.subheader("Estoque Atualizado:")
        if not st.session_state.df_estoque.empty:
            st.dataframe(st.session_state.df_estoque, use_container_width=True)
            csv_estoque = st.session_state.df_estoque.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar Estoque Atualizado (CSV)",
                data=csv_estoque,
                file_name="estoque_gbs_atualizado.csv",
                mime="text/csv",
            )
            # Para XLSX, precisaríamos de uma lib adicional para Streamlit Cloud
            # st.download_button(
            #     label="Baixar Estoque Atualizado (Excel)",
            #     data=st.session_state.df_estoque.to_excel(index=False, engine='openpyxl').read(),
            #     file_name="estoque_gbs_atualizado.xlsx",
            #     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            # )
            st.warning("O download em Excel (XLSX) direto no Streamlit Community Cloud pode exigir configurações adicionais. O CSV é mais garantido.")
        else:
            st.info("Estoque vazio para download.")

        st.subheader("Histórico de Pedidos Processados:")
        if not st.session_state.df_pedidos.empty:
            st.dataframe(st.session_state.df_pedidos, use_container_width=True)
            csv_pedidos = st.session_state.df_pedidos.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar Histórico de Pedidos (CSV)",
                data=csv_pedidos,
                file_name="pedidos_gbs_historico.csv",
                mime="text/csv",
            )
            st.warning("O download em Excel (XLSX) direto no Streamlit Community Cloud pode exigir configurações adicionais. O CSV é mais garantido.")
        else:
            st.info("Nenhum pedido no histórico para download.")


if __name__ == "__main__":
    main()
