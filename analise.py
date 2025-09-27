# --- CÓDIGO COMPLETO E ATUALIZADO ---
# Análise e Detecção Inteligente de Pirataria

import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.ticker import FuncFormatter

# Etapa 0: Configuração de Estilo para os Gráficos
def setup_visual_style():
    """Define um estilo visual padrão para todos os gráficos."""
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (12, 7)
    plt.rcParams['axes.titlesize'] = 18
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12
    plt.rcParams['figure.dpi'] = 100

# Etapa 1: Leitura e Limpeza dos Dados
def load_and_clean_data(filepath):
    """Lê o arquivo CSV, renomeia colunas e faz a limpeza inicial."""
    print("Iniciando a leitura e limpeza dos dados...")
    
    try:
        # CORREÇÃO: Utilizando o separador de vírgula ','
        df = pd.read_csv(filepath, sep=',')
    except FileNotFoundError:
        print(f"Erro: Arquivo '{filepath}' não encontrado. Certifique-se de que ele está na mesma pasta que o script.")
        return None

    # Renomeia as colunas do CSV para os nomes que o script espera.
    colunas_para_renomear = {
        'nome_produto': 'titulo',
        'preco_produto': 'preco',
        'reviews_nota_media': 'avaliacao_nota',
        'reviews_quantidade_total': 'avaliacao_numero'
        # Adicione aqui outras colunas se necessário, ex: 'detalhes': 'descricao'
    }
    df.rename(columns=colunas_para_renomear, inplace=True)

    def parse_brazilian_price(price_str):
        if pd.isna(price_str): return np.nan
        try:
            s = str(price_str).replace('R$', '').strip()
            s = s.replace('.', '').replace(',', '.')
            return float(s)
        except (ValueError, TypeError): return np.nan

    if 'preco' in df.columns:
        df['preco'] = df['preco'].apply(parse_brazilian_price)
    
    if 'avaliacao_nota' in df.columns:
        df['avaliacao_nota'] = pd.to_numeric(df['avaliacao_nota'].astype(str).str.replace(',', '.'), errors='coerce')
    
    if 'avaliacao_numero' in df.columns:
        # CORREÇÃO: Tratamento do FutureWarning
        df['avaliacao_numero'] = df['avaliacao_numero'].fillna(0)
        df['avaliacao_numero'] = df['avaliacao_numero'].astype(int)

    # Remove linhas onde o preço ou o título são nulos
    df.dropna(subset=['preco', 'titulo'], inplace=True)
    
    print("Limpeza concluída. Resumo dos dados:")
    print(df.info())
    print("\nVerificando os dados limpos (5 primeiras linhas):")
    print(df[['titulo', 'preco', 'avaliacao_numero']].head())
    return df

# Etapa 2: Enriquecimento da Base de Dados
def enrich_data(df):
    """Cria novas colunas analíticas para aprofundar a análise."""
    print("\nIniciando o enriquecimento dos dados...")

    def categorize_product(title):
        title_lower = title.lower()
        if 'notebook' in title_lower or 'laptop' in title_lower:
            return 'Notebook'
        if 'impressora' in title_lower:
            return 'Impressora'
        return 'Suprimento de Impressão'
    df['categoria_produto'] = df['titulo'].apply(categorize_product)

    # Lógica de compatibilidade aprimorada
    df['compatibilidade'] = np.where(df['titulo'].str.contains('compativel|compatível|gen[eé]rico|similar|tipo|remanufaturado', case=False, na=False, regex=True), 'Compatível', 'Original')
    df['capacidade'] = np.where(df['titulo'].str.contains('XL', case=False, na=False), 'XL (Alto Rendimento)', 'Padrão')
    df['modelo_cartucho'] = df['titulo'].str.extract(r'\b(662|664|667|954|122)\b', expand=False).fillna('Outro')
    
    # --- MELHORIA: Extrair rendimento do TÍTULO ---
    def extract_yield(text):
        if not isinstance(text, str): return np.nan
        match = re.search(r'(\d+)\s*(p[aá]ginas|pg|págs)\b', text, re.IGNORECASE)
        return int(match.group(1)) if match else np.nan
    
    df['rendimento_paginas'] = df['titulo'].apply(extract_yield)
    df['custo_por_pagina'] = np.where(df['rendimento_paginas'] > 0, df['preco'] / df['rendimento_paginas'], np.nan)
    
    if df['custo_por_pagina'].notna().sum() > 0:
        print(f"Sucesso: Rendimento extraído do título para {df['custo_por_pagina'].notna().sum()} produtos.")
    else:
        print("Aviso: Não foi possível extrair o rendimento do título dos produtos.")

    print("Enriquecimento concluído.")
    return df

# Etapa 3: Aplicação da Inteligência de Detecção
def detect_piracy_indicators(df):
    """Aplica regras de negócio para sinalizar produtos suspeitos."""
    print("\nIniciando a detecção de indicadores de pirataria...")
    
    df['alerta_suspeita'] = False
    df['motivo_suspeita'] = ''

    # Regra 1: Preço muito abaixo da média para produtos "Originais"
    avg_price_original = df[df['compatibilidade'] == 'Original'].groupby('modelo_cartucho')['preco'].mean().to_dict()
    price_threshold = 0.5 

    def check_price_anomaly(row):
        if row['compatibilidade'] == 'Original' and row['modelo_cartucho'] in avg_price_original:
            avg_price = avg_price_original[row['modelo_cartucho']]
            if row['preco'] < (avg_price * price_threshold):
                row['alerta_suspeita'] = True
                row['motivo_suspeita'] += '[Preço Anômalo para Original] '
        return row
    df = df.apply(check_price_anomaly, axis=1)

    # Regra 2: Custo por página extremamente baixo
    cost_threshold = 0.01
    low_cost_mask = (df['custo_por_pagina'].notna()) & (df['custo_por_pagina'] < cost_threshold)
    df.loc[low_cost_mask, 'alerta_suspeita'] = True
    df.loc[low_cost_mask, 'motivo_suspeita'] += '[Custo por Página Suspeito] '

    # Regra 3: Produto "Compatível" com pouquíssimas ou nenhuma avaliação
    review_threshold = 5
    compatible_low_reviews_mask = (df['compatibilidade'] == 'Compatível') & (df['avaliacao_numero'] < review_threshold)
    df.loc[compatible_low_reviews_mask, 'alerta_suspeita'] = True
    df.loc[compatible_low_reviews_mask, 'motivo_suspeita'] += '[Compatível com Baixa Reputação] '

    # --- MELHORIA: Nova Regra 4 - Reputação do Vendedor ---
    if 'reputacao_cor' in df.columns:
        bad_reputations = ['vermelho', 'laranja']
        seller_risk_mask = df['reputacao_cor'].str.lower().isin(bad_reputations)
        df.loc[seller_risk_mask, 'alerta_suspeita'] = True
        df.loc[seller_risk_mask, 'motivo_suspeita'] += '[Vendedor com Reputação Ruim] '
        print("Sucesso: Regra de reputação do vendedor aplicada.")
    else:
        print("Aviso: Coluna 'reputacao_cor' não encontrada. Regra do vendedor ignorada.")

    print("Detecção concluída.")
    return df

# Etapa 4: Análise e Geração de Gráficos
def generate_visualizations(df):
    """Gera e salva os gráficos para a análise exploratória."""
    print("\nIniciando a geração das visualizações...")

    df_suprimentos = df[df['categoria_produto'] == 'Suprimento de Impressão'].copy()
    
    if df_suprimentos.empty:
        print("Nenhum 'Suprimento de Impressão' encontrado para gerar gráficos.")
        return

    price_limit = df_suprimentos['preco'].quantile(0.95)
    df_filtered_price = df_suprimentos[df_suprimentos['preco'] <= price_limit]
    
    # Gráfico 1: Análise de Preços
    plt.figure()
    sns.boxplot(x='compatibilidade', y='preco', data=df_filtered_price, hue='compatibilidade', palette='viridis', order=['Original', 'Compatível'], legend=False)
    plt.title('Distribuição de Preços de Suprimentos')
    plt.xlabel('Tipo de Cartucho')
    plt.ylabel('Preço (R$)')
    plt.tight_layout()
    plt.savefig('grafico_1_preco_vs_compatibilidade.png')
    print("Gráfico 1 salvo.")
    plt.close()

    # Gráfico 2: Relação entre Preço e Avaliação
    plt.figure()
    sns.scatterplot(x='preco', y='avaliacao_nota', hue='compatibilidade', data=df_filtered_price.dropna(subset=['avaliacao_nota']), palette='magma', s=100, alpha=0.8)
    plt.title('Relação entre Preço e Nota de Avaliação')
    plt.xlabel('Preço (R$)')
    plt.ylabel('Nota Média de Avaliação')
    plt.legend(title='Compatibilidade')
    plt.tight_layout()
    plt.savefig('grafico_2_preco_vs_avaliacao.png')
    print("Gráfico 2 salvo.")
    plt.close()

    print("Visualizações geradas.")

# Etapa 5: Execução Principal
if __name__ == '__main__':
    setup_visual_style()
    
    # Altere aqui para o caminho do seu arquivo CSV
    csv_filepath = 'dataset_mercado_livre.csv' 
    df_cleaned = load_and_clean_data(csv_filepath)
    
    if df_cleaned is not None:
        df_enriched = enrich_data(df_cleaned.copy())
        
        df_final = detect_piracy_indicators(df_enriched)
        
        print("\n--- Amostra da Tabela com Análise de Suspeita ---")
        colunas_para_exibir = [
            'titulo', 'preco', 'compatibilidade', 'modelo_cartucho', 
            'custo_por_pagina', 'alerta_suspeita', 'motivo_suspeita'
        ]
        colunas_existentes = [col for col in colunas_para_exibir if col in df_final.columns]
        print(df_final[colunas_existentes].head(10).to_string())

        df_suspeitos = df_final[df_final['alerta_suspeita'] == True]
        print(f"\n\n--- RELATÓRIO DE PRODUTOS SINALIZADOS ({len(df_suspeitos)} encontrados) ---")
        if not df_suspeitos.empty:
            print(df_suspeitos[colunas_existentes].to_string())
        else:
            print("Nenhum produto suspeito foi detectado pelas regras atuais.")

        try:
            enriched_csv_filename = 'dados_enriquecidos_com_alertas.csv'
            df_final.to_csv(enriched_csv_filename, index=False, sep=';', encoding='utf-8-sig')
            print(f"\nDataFrame final salvo com sucesso em: {enriched_csv_filename}")
        except Exception as e:
            print(f"\nErro ao salvar o CSV final: {e}")
        
        generate_visualizations(df_final)
        
        print("\nAnálise e Detecção concluídas com sucesso!")