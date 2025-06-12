import streamlit as st
import pandas as pd
import math
import io 
from datetime import datetime

# --- Configurações da Chapa Padrão (Fixas) ---
LARGURA_CHAPA_PADRAO = 1680  # mm
COMPRIMENTO_CHAPA_PADRAO = 2600  # mm

# --- Lógica de Cálculo Automático de Caixas por Chapa Padrão e Retalhos ---
def calcular_aproveitamento_e_retalhos(largura_corte, comprimento_corte):
    lp = LARGURA_CHAPA_PADRAO
    cp = COMPRIMENTO_CHAPA_PADRAO

    # Orientação 1
    num_pecas_largura_1 = math.floor(lp / largura_corte)
    num_pecas_comprimento_1 = math.floor(cp / comprimento_corte)
    qtd_caixas_orientacao_1 = num_pecas_largura_1 * num_pecas_comprimento_1

    sobra_largura_1 = lp - (num_pecas_largura_1 * largura_corte)
    sobra_comprimento_1 = cp - (num_pecas_comprimento_1 * comprimento_corte)
    retalho_1_orientacao_1 = f"{sobra_largura_1}x{cp}"
    retalho_2_orientacao_1 = f"{lp}x{sobra_comprimento_1}"

    # Orientação 2
    num_pecas_largura_2 = math.floor(lp / comprimento_corte)
    num_pecas_comprimento_2 = math.floor(cp / largura_corte)
    qtd_caixas_orientacao_2 = num_pecas_largura_2 * num_pecas_comprimento_2
    
    sobra_largura_2 = lp - (num_pecas_largura_2 * comprimento_corte)
    sobra_comprimento_2 = cp - (num_pecas_comprimento_2 * largura_corte)
    retalho_1_orientacao_2 = f"{sobra_largura_2}x{cp}"
    retalho_2_orientacao_2 = f"{lp}x{sobra_comprimento_2}"

    # Escolher a melhor orientação (maior número de caixas)
    if qtd_caixas_orientacao_1 >= qtd_caixas_orientacao_2:
        return qtd_caixas_orientacao_1, retalho_1_orientacao_1, retalho_2_orientacao_1
    else:
        return qtd_caixas_orientacao_2, retalho_1_orientacao_2, retalho_2_orientacao_2

# --- Função principal do Streamlit ---
def main():
    st.set_page_config(layout="wide", page_title="GBS - Planejamento de Produção")
    st.title("📦 GBS - Planejamento e Controle de Produção")

    # --- Inicialização dos DataFrames na memória (st.session_state) ---
    if 'df_estoque' not in st.session_state:
        st.session_state.df_estoque = pd.DataFrame(columns=[
            'Dimensao_Chapa', 'Tipo_Papelao', 'Gramatura', 'Quantidade_Folhas', 'Peso_m2_kg'
        ])
    if 'df_pedidos' not in st.session_state: # df_pedidos é o log da sessão atual
        st.session_state.df_pedidos = pd.DataFrame(columns=[
            'OS', 'Cliente', 'Descricao_Pedido', 'Valor_Pedido', 'Dimensao_Corte_LxC', 
            'Quantidade_Caixas', 'Tipo_Papelao_Pedido', 'Gramatura_Pedido', 
            'Chapas_Padrao_Necessarias', 'Retalhos_Gerados_Dimensoes', 
            'Retalhos_1680x1240_Gerados', 'Retalhos_384x1360_Gerados', 
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
                # O arquivo é lido como bytes e passado para pandas
                st.session_state.df_estoque = pd.read_csv(uploaded_file, sep=';') # Considera ; como separador
                st.success("Estoque carregado com sucesso! Lembre-se que este estoque é válido apenas para esta sessão.")
            except Exception as e:
                st.error(f"Erro ao carregar o arquivo CSV: {e}. Verifique o formato, o separador (deve ser ponto e vírgula) e as colunas.")
        
        st.subheader("Adicionar Novo Item ou Atualizar Quantidade")
        with st.form("form_estoque"):
            col1, col2 = st.columns(2)
            with col1:
                dimensao = st.text_input("Dimensão Chapa (ex: 1680x2600)", key="estoque_dimensao_input").strip()
                tipo_papelao = st.text_input("Tipo de Papelão (ex: Onda C)", key="estoque_tipo_input").strip()
            with col2:
                gramatura = st.number_input("Gramatura (g/m²)", min_value=1, value=370, key="estoque_gramatura_input")
                quantidade = st.number_input("Quantidade de Folhas", min_value=0, value=0, key="estoque_quantidade_input") 
            
            peso_m2_kg = st.number_input("Peso por m² (kg/m² - ex: 0.370 para 370g/m²)", min_value=0.001, value=float(gramatura/1000) if gramatura > 0 else 0.001, format="%.3f", key="estoque_peso_m2_input")

            adicionar_estoque_btn = st.form_submit_button("Adicionar/Atualizar Item no Estoque")
            
            if adicionar_estoque_btn:
                if not dimensao or not tipo_papelao or gramatura <= 0 or peso_m2_kg <= 0:
                    st.error("Por favor, preencha 'Dimensão', 'Tipo de Papelão', 'Gramatura' e 'Peso por m²' corretamente.")
                else:
                    item_existente_idx = st.session_state.df_estoque[
                        (st.session_state.df_estoque['Dimensao_Chapa'] == dimensao) &
                        (st.session_state.df_estoque['Tipo_Papelao'] == tipo_papelao) &
                        (st.session_state.df_estoque['Gramatura'] == gramatura)
                    ].index

                    if not item_existente_idx.empty:
                        st.session_state.df_estoque.loc[item_existente_idx, 'Quantidade_Folhas'] += quantidade
                        st.session_state.df_estoque.loc[item_existente_idx, 'Peso_m2_kg'] = peso_m2_kg 
                        st.success(f"Quantidade de {dimensao} {tipo_papelao} {gramatura}g/m² atualizada para {st.session_state.df_estoque.loc[item_existente_idx, 'Quantidade_Folhas'].iloc[0]}.")
                    else:
                        novo_item = pd.DataFrame([{
                            'Dimensao_Chapa': dimensao,
                            'Tipo_Papelao': tipo_papelao,
                            'Gramatura': gramatura,
                            'Quantidade_Folhas': quantidade,
                            'Peso_m2_kg': peso_m2_kg
                        }])
                        st.session_state.df_estoque = pd.concat([st.session_state.df_estoque, novo_item], ignore_index=True)
                        st.success(f"Item de estoque {dimensao} adicionado com sucesso!")
                    
                    st.session_state.df_estoque = st.session_state.df_estoque.sort_values(by=['Dimensao_Chapa', 'Tipo_Papelao', 'Gramatura']).reset_index(drop=True)


        st.subheader("Estoque Atual na Memória:")
        if not st.session_state.df_estoque.empty:
            st.dataframe(st.session_state.df_estoque, use_container_width=True)
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
                    chapa_padrao_estoque_idx = st.session_state.df_estoque[
                        (st.session_state.df_estoque['Dimensao_Chapa'] == f"{LARGURA_CHAPA_PADRAO}x{COMPRIMENTO_CHAPA_PADRAO}") &
                        (st.session_state.df_estoque['Tipo_Papelao'] == tipo_papelao_pedido) &
                        (st.session_state.df_estoque['Gramatura'] == gramatura_pedido)
                    ].index

                    if chapa_padrao_estoque_idx.empty:
                        st.error(f"Erro: Chapa padrão {LARGURA_CHAPA_PADRAO}x{COMPRIMENTO_CHAPA_PADRAO} com Tipo '{tipo_papelao_pedido}' e Gramatura '{gramatura_pedido}g/m²' não encontrada no estoque. Adicione-a primeiro na aba 'Lançar Estoque'.")
                    else:
                        # --- Cálculos do Pedido ---
                        qtd_caixas_por_chapa_padrao, retalho1_dim, retalho2_dim = \
                            calcular_aproveitamento_e_retalhos(dim_largura_corte, dim_comprimento_corte)

                        if qtd_caixas_por_chapa_padrao == 0:
                            st.error(f"Erro: A chapa de corte {dim_largura_corte}x{dim_comprimento_corte} não cabe na chapa padrão {LARGURA_CHAPA_PADRAO}x{COMPRIMENTO_CHAPA_PADRAO} em nenhuma orientação. Verifique as dimensões.")
                        else:
                            num_folhas_padrao_necessarias = math.ceil(qtd_caixas / qtd_caixas_por_chapa_padrao)

                            # Verificar se há chapas suficientes no estoque
                            estoque_atual_chapa_padrao_qty = st.session_state.df_estoque.loc[chapa_padrao_estoque_idx, 'Quantidade_Folhas'].iloc[0]
                            if estoque_atual_chapa_padrao_qty < num_folhas_padrao_necessarias:
                                st.warning(f"Aviso: Estoque insuficiente de chapas {LARGURA_CHAPA_PADRAO}x{COMPRIMENTO_CHAPA_PADRAO} ({tipo_papelao_pedido}, {gramatura_pedido}g/m²). Necessário: {num_folhas_padrao_necessarias}, Disponível: {estoque_atual_chapa_padrao_qty}. O estoque será abatido.")
                            
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
                            retalhos_gerados_info = {} 
                            
                            if retalho1_dim != "0x2600" and retalho1_dim != "1680x0": 
                                retalhos_gerados_info[retalho1_dim] = retalhos_gerados_info.get(retalho1_dim, 0) + num_folhas_padrao_necessarias
                            
                            if retalho2_dim != "0x2600" and retalho2_dim != "1680x0": 
                                retalhos_gerados_info[retalho2_dim] = retalhos_gerados_info.get(retalho2_dim, 0) + num_folhas_padrao_necessarias
                            
                            for dim_retalho, qty_retalho in retalhos_gerados_info.items():
                                item_retalho_idx = st.session_state.df_estoque[
                                    (st.session_state.df_estoque['Dimensao_Chapa'] == dim_retalho) &
                                    (st.session_state.df_estoque['Tipo_Papelao'] == tipo_papelao_pedido) &
                                    (st.session_state.df_estoque['Gramatura'] == gramatura_pedido)
                                ].index
                                if not item_retalho_idx.empty:
                                    st.session_state.df_estoque.loc[item_retalho_idx, 'Quantidade_Folhas'] += qty_retalho
                                else:
                                    novo_retalho = pd.DataFrame([{
                                        'Dimensao_Chapa': dim_retalho,
                                        'Tipo_Papelao': tipo_papelao_pedido,
                                        'Gramatura': gramatura_pedido,
                                        'Quantidade_Folhas': qty_retalho,
                                        'Peso_m2_kg': peso_m2_kg_estoque
                                    }])
                                    st.session_state.df_estoque = pd.concat([st.session_state.df_estoque, novo_retalho], ignore_index=True)
                            
                            st.session_state.df_estoque = st.session_state.df_estoque.sort_values(by=['Dimensao_Chapa', 'Tipo_Papelao', 'Gramatura']).reset_index(drop=True)

                            # --- Registrar Pedido no Log da Sessão (st.session_state.df_pedidos) ---
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
                                'Retalhos_Gerados_Dimensoes': str(list(retalhos_gerados_info.keys())),
                                'Retalhos_1680x1240_Gerados': retalhos_gerados_info.get("1680x1240", 0),
                                'Retalhos_384x1360_Gerados': retalhos_gerados_info.get("384x1360", 0),
                                'Peso_Total_Pedido_kg': peso_total_pedido_kg,
                                'Data_Processamento': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }])
                            st.session_state.df_pedidos = pd.concat([st.session_state.df_pedidos, novo_pedido_log], ignore_index=True)

                            st.success(f"Pedido OS: {os_pedido} processado e estoque atualizado na memória!")
                            st.info(f"O aproveitamento para a chapa de corte {dim_largura_corte}x{dim_comprimento_corte} na chapa padrão {LARGURA_CHAPA_PADRAO}x{COMPRIMENTO_CHAPA_PADRAO} é de **{qtd_caixas_por_chapa_padrao} caixas por chapa padrão.**")
                            st.write(f"Você precisará de **{num_folhas_padrao_necessarias}** chapas padrão de {LARGURA_CHAPA_PADRAO}x{COMPRIMENTO_CHAPA_PADRAO}.")
                            st.write(f"Serão gerados: {retalhos_gerados_info}")
                            
                            # Limpar campos do formulário de pedido
                            st.session_state.pedido_os_input = ''
                            st.session_state.pedido_cliente_input = ''
                            st.session_state.pedido_descricao_input = ''
                            st.session_state.pedido_valor_input = 0.0
                            st.session_state.pedido_dim_largura_input = 0
                            st.session_state.pedido_dim_comprimento_input = 0
                            st.session_state.pedido_qtd_caixas_input = 0
                            st.session_state.pedido_tipo_input = ''
                            st.session_state.pedido_gramatura_input = 0


        st.subheader("Últimos Pedidos Processados NESTA Sessão:")
        if not st.session_state.df_pedidos.empty:
            st.dataframe(st.session_state.df_pedidos.tail(5), use_container_width=True)
        else:
            st.info("Nenhum pedido processado nesta sessão ainda.")

    with tab_relatorios:
        st.header("📊 Relatórios e Downloads")
        st.write("Baixe suas planilhas para salvar os dados permanentemente no seu computador. Lembre-se de fazer o upload do estoque na próxima sessão.")

        st.subheader("Estoque Atual na Memória:")
        if not st.session_state.df_estoque.empty:
            st.dataframe(st.session_state.df_estoque, use_container_width=True)
            
            # --- Botão de Download do Estoque em CSV ---
            csv_estoque = st.session_state.df_estoque.to_csv(index=False, sep=';').encode('utf-8') 
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
            st.dataframe(st.session_state.df_pedidos, use_container_width=True)
            
            # --- Botão de Download do Histórico de Pedidos em CSV ---
            csv_pedidos = st.session_state.df_pedidos.to_csv(index=False, sep=';').encode('utf-8')
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





    
  

       
       
                 
                      
                               
                      
                      
             
          


if __name__ == "__main__":
    main()
