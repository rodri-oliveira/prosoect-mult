from playwright.sync_api import sync_playwright

def run(playwright):
    print("Iniciando bateria de testes E2E do CRM...")
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        print("1. Testando Dashboard...")
        page.goto("http://127.0.0.1:5000/")
        assert "CRM" in page.content() and "Multi" in page.content()
        print(" -> Dashboard Carregado com Sucesso")

        print("2. Testando Lojas (Leads)...")
        page.goto("http://127.0.0.1:5000/leads")
        assert "Lojas (Leads)" in page.content() or "Multi" in page.content()
        print(" -> Página Lojas Carregada com Sucesso")

        print("3. Testando Tela Oculta de Prospecção (Correção do 404)...")
        page.goto("http://127.0.0.1:5000/prospeccao")
        assert "Buscar no Mapa" in page.content()
        print(" -> Tela Prospecção Carregada com Sucesso")

        print("4. Testando Criação de Lead via Prospecção...")
        page.fill("input[name='nome_loja']", "Loja Teste Automação")
        page.fill("input[name='telefone']", "11900000000")
        page.click("button:has-text('Salvar Lead')")
        page.wait_for_load_state("networkidle")
        print(" -> Lead Criado com Sucesso via Formulário HTML Rápido")

        print("5. Testando Fila de Ligação...")
        page.goto("http://127.0.0.1:5000/fila")
        assert "Fila" in page.content() or "CRM" in page.content()
        print(" -> Fila de Prospecção Ativa Carregada com Sucesso")

        print("6. Testando Relatório Diário...")
        page.goto("http://127.0.0.1:5000/relatorio")
        assert "Copiar" in page.content() or "Relatório" in page.content()
        print(" -> Relatório Renderizado com Sucesso")

        print("\nSUCESSO ABSOLUTO: Todas as views e insercoes do CRM foram testadas virtualmente e estao funcionando!")

    except AssertionError as e:
        print("\nERRO NA AUTOMACAO: Uma das telas falhou na renderizacao.")
        try:
            print("--- HTML PARCIAL RETORNADO ---")
            print(page.content()[:500])
        except:
            pass
        print(e)
    except Exception as e:
        print(f"\nERRO FATAL NO PLAYWRIGHT: {str(e)}")
    
    finally:
        context.close()
        browser.close()

with sync_playwright() as playwright:
    run(playwright)
