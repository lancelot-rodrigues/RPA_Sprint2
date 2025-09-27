# Relatório Técnico: Automação Inteligente de Detecção de Pirataria

## 1. Introdução

Este documento detalha a implementação de um fluxo de **Hiperautomação** projetado para identificar automaticamente indícios de pirataria em produtos de e-commerce.

A solução combina um **robô de automação de processos (RPA)** para coleta de dados com um **script de análise inteligente (IA Leve)** para classificação e geração de alertas.

O objetivo é transformar uma base de dados de produtos em um sistema automatizado capaz de aplicar análises, identificar produtos suspeitos e gerar relatórios acionáveis, criando um pipeline de monitoramento contínuo.

---

## 2. Arquitetura da Solução e Fluxo de Execução

O pipeline foi estruturado de forma **sequencial e modular**, garantindo reprodutibilidade e manutenção simples.

### Etapa 1: Coleta de Dados (RPA)

* Um robô de scraping navega pela plataforma de e-commerce.
* Extrai dados brutos de anúncios (título, preço, vendedor, avaliações, etc.).
* Os dados são salvos em `dataset_mercado_livre.csv` para servir de input.

### Etapa 2: Limpeza e Estruturação de Dados

* O script `analise.py` carrega o CSV.
* Colunas renomeadas para padrão unificado.
* Conversão de preços para **float** e padronização de colunas numéricas.
* Linhas sem informações essenciais (preço ou título) são descartadas.

### Etapa 3: Enriquecimento de Dados

Novas features criadas:

* **compatibilidade** → "Original" ou "Compatível" (palavras-chave).
* **modelo_cartucho** → extraído via regex (ex: 664, 122).
* **rendimento_paginas** → promessa de rendimento (ex: "700 páginas").
* **custo_por_pagina** → custo-benefício, métrica chave para anomalias.

### Etapa 4: Análise e Classificação (IA Leve)

* Heurísticas e regras de negócio aplicadas a cada produto.
* Produtos suspeitos recebem `alerta_suspeita = True` + motivo.

### Etapa 5: Geração de Saídas (Relatórios)

* Arquivo final: `dados_enriquecidos_com_alertas.csv`.
* Relatório de produtos sinalizados no console.
* Geração de **gráficos (.png)** para análise exploratória.

---

## 3. Heurísticas e Regras de Negócio

A **IA Leve** é baseada em regras, oferecendo alta interpretabilidade.

* **Regra 1: Preço Anômalo para Produtos Originais**

  * Se preço < 50% da média do modelo → sinalizado.

* **Regra 2: Custo por Página Suspeito**

  * Se custo/página < R$ 0,01 → sinalizado.

* **Regra 3: Produtos Compatíveis com Baixa Reputação**

  * Se compatível + menos de 5 reviews → sinalizado.

* **Regra 4: Reputação do Vendedor**

  * Se `reputacao_cor` = vermelho/laranja → sinalizado.

---

## 4. Exemplos de Detecções

<img width="1469" height="757" alt="image" src="https://github.com/user-attachments/assets/67222285-60d5-4211-a4a3-43cc7086cd19" />


---

## 5. Código-Fonte (Estrutura Principal)

Principais funções:

* `load_and_clean_data` → limpeza e estruturação.
* `enrich_data` → enriquecimento.
* `detect_piracy_indicators` → aplicação das regras de detecção.


---

## 6. Instruções para Execução

### Pré-requisitos

* Python **3.8+**
* Bibliotecas:

<img width="310" height="51" alt="image" src="https://github.com/user-attachments/assets/ccd7c3c2-f519-4541-bb41-5a9855f38f2b" />


### Estrutura de Pastas

```
/seu_projeto/
|-- analise.py
|-- dataset_mercado_livre.csv
```

### Execução

<img width="241" height="48" alt="image" src="https://github.com/user-attachments/assets/43995db0-63f6-4d0a-8319-2b583c268f6f" />


Saídas:

* `dados_enriquecidos_com_alertas.csv`
* gráficos `.png`

---

## 7. Conclusão

A solução cumpre os requisitos centrais do entregável, estabelecendo um **pipeline funcional de detecção de pirataria**.

Com heurísticas e regras de negócio, transforma dados brutos em inteligência acionável. A análise de reputação e extração de dados do título demonstram adaptabilidade mesmo com fontes limitadas.

O projeto serve como **base sólida para futuras expansões**, como:

* Modelos de machine learning.
* Sistemas de alerta em tempo real.
