import os
import re
import time
import random
import csv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from playwright_stealth import Stealth

#Configurações Iniciais
LISTA_DE_BUSCAS = [
    "cartucho hp original",
    "cartucho de tinta hp",
    "tinta para impressora hp",
    "cartucho hp 664",
    "cartucho hp 662",
    "cartucho hp preto",
    "cartucho hp colorido",
    "kit cartucho hp preto e colorido",
    "kit cartucho de tinta original HP",
    "cartucho HP",
    "cartucho compatível HP",
    "cartucho hp 60xl",
    "cartucho hp 901",
    "cartucho hp 21 e 22",
    "cartucho hp 92",
    "cartucho hp 93",
    "cartucho hp 934",
    "cartucho hp 951xl",
    "kit 4 cartuchos hp",
    "combo cartucho hp 664",
    "pack cartucho hp 667xl",
    "cartucho hp multipack",
    "cartucho HP combo pack",
    "cartucho hp alto rendimento"
    ]
NOME_ARQUIVO_SAIDA = "dataset_mercado_livre.csv"
NUMERO_PAGINAS_SCRAPE = 60 #Aumente para coletar mais dados

#User-Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
]

def extrair_dados_produto(page, url_produto):
    print(f"   > Extraindo dados de: {url_produto}")
    try:
        page.goto(url_produto, wait_until='domcontentloaded', timeout=60000)
        page.mouse.wheel(0, 800)
        time.sleep(random.uniform(1, 2.5))
        
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')

        dados = {}

        #Produto e features
        try: dados['nome_produto'] = soup.select_one('h1.ui-pdp-title').text.strip()
        except: dados['nome_produto'] = 'N/A'
        try:
            preco_inteiro = soup.select_one('span.andes-money-amount__fraction').text.strip()
            preco_centavos_element = soup.select_one('span.andes-money-amount__cents')
            preco_centavos = preco_centavos_element.text.strip() if preco_centavos_element else '00'
            dados['preco_produto'] = f"{preco_inteiro.replace('.', '')},{preco_centavos}"
        except: dados['preco_produto'] = 'N/A'
        try:
            subtitle_text = soup.select_one('span.ui-pdp-subtitle').text.strip()
            vendidos_match = re.search(r'(\d+)\s+vendidos', subtitle_text)
            dados['quantidade_vendida'] = int(vendidos_match.group(1)) if vendidos_match else 0
        except: dados['quantidade_vendida'] = 0
        try: dados['nome_vendedor'] = soup.select_one('.ui-pdp-seller__link-trigger-button span:nth-child(2)').text.strip()
        except: dados['nome_vendedor'] = 'N/A'
        try:
            status_text = soup.select_one('.ui-pdp-seller__header__subtitle').text.strip()
            dados['status_vendedor'] = status_text.split('|')[0].strip()
        except: dados['status_vendedor'] = 'Vendedor Comum'
        try:
            reputacao_value = int(soup.select_one('.ui-seller-data-status__thermometer')['value'])
            reputacao_map = {1: 'Vermelho', 2: 'Laranja', 3: 'Amarelo', 4: 'Verde Claro', 5: 'Verde'}
            dados['reputacao_cor'] = reputacao_map.get(reputacao_value, 'N/A')
        except: dados['reputacao_cor'] = 'N/A'
        
        #Features de review
        try: dados['reviews_nota_media'] = float(soup.select_one('p.ui-review-capability__rating__average').text.strip())
        except: dados['reviews_nota_media'] = 0.0
        try:
            reviews_text = soup.select_one('p.ui-review-capability__rating__label').text.strip()
            reviews_match = re.search(r'(\d+)', reviews_text)
            dados['reviews_quantidade_total'] = int(reviews_match.group(1)) if reviews_match else 0
        except: dados['reviews_quantidade_total'] = 0
        
        #Notas
        star_levels = soup.select("li.ui-review-capability-rating__level")
        for i, level in enumerate(star_levels):
            star_number = 5 - i
            try:
                style_attr = level.select_one('span.ui-review-capability-rating__level__progress-bar__fill-background')['style']
                percentage_match = re.search(r'width:([\d\.]+)%', style_attr)
                percentage = float(percentage_match.group(1)) if percentage_match else 0.0
            except:
                percentage = 0.0
            dados[f'reviews_{star_number}_estrelas_pct'] = percentage

        dados['url_produto'] = page.url
        return dados

    except Exception as e:
        print(f"   [ERRO GERAL] Falha crítica ao processar {url_produto}: {e}")
        return None


def main():
    AUTH_FILE = 'auth.json'
    with sync_playwright() as p:
        stealth = Stealth()
        browser = p.chromium.launch(headless=True, args=["--start-maximized"])
        context = None

        #Lógica de login
        if os.path.exists(AUTH_FILE):
            print("Arquivo de autenticação encontrado. Carregando sessão...")
            context = browser.new_context(storage_state=AUTH_FILE, no_viewport=True, user_agent=random.choice(USER_AGENTS))
        else:
            print("Arquivo de autenticação não encontrado. Procedendo com login manual.")
            context = browser.new_context(no_viewport=True, user_agent=random.choice(USER_AGENTS))
            stealth.apply_stealth_sync(context)
            
            page_setup = context.new_page()
            page_setup.goto('https://www.mercadolivre.com.br/login', timeout=90000)
            print("\n" + "="*50 + "\nAÇÃO NECESSÁRIA: Faça o login no navegador.\nApós o sucesso, volte e pressione 'Enter'.\n" + "="*50 + "\n")
            input("Pressione Enter após ter feito o login...")
            context.storage_state(path=AUTH_FILE)
            print(f"Estado de autenticação salvo em '{AUTH_FILE}'.")
            page_setup.close()

        if not os.path.exists(AUTH_FILE): pass
        else: stealth.apply_stealth_sync(context)

        page = context.new_page()
        try:
            with open(NOME_ARQUIVO_SAIDA, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    "nome_produto", "preco_produto", "quantidade_vendida", "nome_vendedor", 
                    "status_vendedor", "reputacao_cor", "reviews_nota_media", 
                    "reviews_quantidade_total", "reviews_5_estrelas_pct", "reviews_4_estrelas_pct", 
                    "reviews_3_estrelas_pct", "reviews_2_estrelas_pct", "reviews_1_estrelas_pct", "url_produto"
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                #Loop através de cada termo de busca
                for termo_busca in LISTA_DE_BUSCAS:
                    print(f"\n{'='*20} INICIANDO BUSCA POR: '{termo_busca}' {'='*20}")
                    
                    termo_formatado = termo_busca.replace(' ', '-')
                    url_busca_atual = f"https://lista.mercadolivre.com.br/{termo_formatado}"
                    
                    for i in range(1, NUMERO_PAGINAS_SCRAPE + 1):
                        print(f"\n--- Acessando página de resultados número {i} ---")
                        page.goto(url_busca_atual, timeout=90000)
                        try:
                            page.wait_for_selector('ol.ui-search-layout', timeout=20000)
                            print("Contêiner de resultados encontrado!")
                        except Exception as e:
                            print(f"ERRO: O contêiner de produtos não carregou. Pulando para o próximo termo. Detalhes: {e}")
                            page.screenshot(path=f'screenshot_erro_{termo_formatado}.png')
                            break #Quebra o loop de páginas e vai para o próximo termo de busca

                        links_produtos = page.locator('a.poly-component__title').evaluate_all("elements => elements.map(element => element.href)")
                        links_produtos = sorted(list(set(links_produtos)))
                        
                        print(f"Encontrados {len(links_produtos)} produtos na página {i}.")
                        if not links_produtos: 
                            print("Nenhum link de produto encontrado nesta página. Indo para a próxima.")
                            #Encontra o botão de próxima página
                            next_button_check = page.locator('a[title="Seguinte"]')
                            if next_button_check.is_visible():
                                url_busca_atual = next_button_check.get_attribute('href')
                                continue
                            else:
                                print("Fim da paginação para este termo.")
                                break

                        for link in links_produtos:
                            time.sleep(random.uniform(2.5, 6)) #Delay para coletas grandes
                            dados_produto = extrair_dados_produto(page, link)
                            if dados_produto: 
                                writer.writerow(dados_produto)
                        
                        next_button = page.locator('a[title="Seguinte"]')
                        if next_button.is_visible(): 
                            url_busca_atual = next_button.get_attribute('href')
                        else:
                            print("Fim da paginação para este termo.")
                            break
        except Exception as e:
            print(f"[ERRO GERAL] Ocorreu um erro: {e}")
        finally:
            print("\nScraping finalizado. Fechando o navegador.")
            browser.close()

if __name__ == "__main__":
    main()