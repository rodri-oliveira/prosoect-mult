# Diretrizes e Regras do Motor de Prospecção B2B (Google Maps)

Este documento serve como o guia definitivo para a calibração, manutenção e criação de novos segmentos no motor de busca de prospecção do CRM. O objetivo exclusivo do motor é encontrar **CNPJs Comerciais de revenda em volume (B2B)**, ignorando o varejo massivo e as prestadoras de serviços básicos.

---

## 1. Regras de Ouro (O que FAZER)

### 1.1. Foco em Hierarquia de Canal (A Tropa de Elite)
Todo segmento deve ser estruturado para buscar, prioritariamente, estes 3 níveis de compradores:
1. **O Alto Volume:** "atacadista [segmento]", "distribuidor [segmento]", "revenda [segmento]".
2. **O Médio Comércio (Varejo Regional):** Lojas de médio porte (ex: "papelaria", "loja de utilidades", "loja de móveis", "bazar"). *Estas empresas frequentemente vendem eletrônicos, mouses e eletroportáteis de curva B/C em paralelo à sua operação principal.*
3. **Ponto de Queima (Curva C e Lotes):** "outlet [segmento]", "saldão [segmento]".

### 1.2. A "Guilhotina" Python (Filtro de Servidor)
O banco de dados do Google Maps falha cerca de 15% das vezes ao respeitar filtros de exclusão visuais (ex: `-"conserto"`). Portanto, é **obrigatório** manter a variável `server_exclusions` (a Guilhotina Python) atualizada na função `_filter_large_retail()`. 
*Se uma palavra como "conserto", "assistência técnica" ou "reparo" aparecer no nome da loja listada, o Python cortará o lead antes dele ir para a tela do vendedor.*

---

## 2. Pecados Capitais (O que NÃO FAZER)

### 2.1. NUNCA busque por Produtos Específicos (A Maldição da Prateleira)
**❌ Errado:** Buscar por `"mouse"`, `"ssd"`, `"air fryer"`, `"panela de pressão"`, `"torradeira"`.
**🔴 O problema:** O Google Maps não é um catálogo de produtos. Se você buscar "torradeira", ele trará a Casas Bahia (inútil B2B) ou a assistência técnica consertando uma torradeira.
**✅ Correto:** Buscar pelo **perfil da loja** que vende esse produto (ex: `"loja de utilidades"`, `"bazar e eletro"`, `"papelaria e informática"`).

### 2.2. NUNCA use palavras que ativam Supermercados e Alimentação
**❌ Errado:** Usar o termo `"atacadão de utilidades"` ou `"mercadão de utilidades"`.
**🔴 O problema:** O mapa semântico do Google atrela as palavras "atacadão" e "mercadão" fortemente ao setor alimentício brasileiro. Se jogar essas palavras, sua prospecção de eletrônicos será imediatamente poluída por `Rotisserias`, `Açougues` e `Supermercados`.
**✅ Correto:** Usar `"comercial importadora"`, `"bazar e presentes"`, `"lojas de variedades"`.

### 2.3. Cuidado com Numerais Isolados
**❌ Errado:** Buscar por `"loja de 1,99"`.
**🔴 O problema:** A API confunde a formatação de preço do número com coordenadas de CEP ou ruas, retornando pinos vazios em terminais de ônibus ou marcadores com o nome da cidade (ex: `"Adamantina-SP"`).
**✅ Correto:** Usar `"loja de preço único"`, `"loja de utilidades e presentes"`.

### 2.4. NUNCA Sobreponha Perfis (Regra da Exclusividade)
Se um segmento de **Utilidades e Variedades** já foi criado para procurar potes de plástico e brinquedos, retire as palavras "bazar" e "utilidades" dos segmentos de **Eletroportáteis** e **Informática**. A sobreposição duplica o custo de API magnifica e polui a tela do vendedor misturando o cara que compra placa de vídeo com o cara que compra Tupperware.

---

## 3. Guia Detalhado de Segmentos Atualizados

Abaixo está o registro de como cada área foi lapidada com dados reais empíricos para servir de referência base.

### 🖥️ Informática
*   **FOCO:** Revendas de tecnologia, papelarias que vendem eletrônicos, lojas multimarcas.
*   **ALVOS PRINCIPAIS:** `"distribuidor informática"`, `"loja de eletrônicos"`, `"papelaria e informática"`, `"suprimentos de informática"`, `"saldão informática"`.
*   **O QUE FOI CORTADO:** Termos de hardware isolados (`"mouse"`, `"nobreak"`) que não traziam CNPJs novos, e assistências técnicas rasas (`-"manutenção"`).

### ⚡ Eletroportáteis
*   **FOCO:** Móveis/Eixo Casa regional, queima de saldo e distribuidores de linha branca.
*   **ALVOS PRINCIPAIS:** `"loja de eletrodomésticos"`, `"distribuidor eletrodomésticos"`, `"outlet eletrodomésticos"`.
*   **O QUE FOI CORTADO:** Termos de produto único (`"air fryer"`) e todo o cruzamento inútil com lojas pequenas de utilidades (que agora têm segmento próprio).

### 🎁 Utilidades e Variedades
*   **FOCO:** O *pote de ouro* Multikids e compra de impulso da curva B/C (Brinquedos, fones de baixo custo, eletrônica barata).
*   **ALVOS PRINCIPAIS:** `"loja de utilidades"`, `"bazar e presentes"`, `"comercial importadora"`, `"loja de variedades"`.
*   **O QUE FOI CORTADO:** A maldita palavra `"atacadão"` para impedir invasão de rotisserias e açougues, e números quebrados (`"1,99"`).

### 📱 Celulares
*   **FOCO (Próximos passos baseados na regra):** Fugir de Apple Stores, assistências de conserto de tela, focando 100% em **distribuidores de cases, cabos e powerbanks** para vitrine.
*   **ALVOS PRINCIPAIS:** `"distribuidor acessórios celular"`, `"loja de capinhas de celular"`, `"acessórios para celular"`.

### 🎧 Áudio e Vídeo
*   **FOCO (Próximos passos baseados na regra):** Evitar caixas bluetooth comuns de varejo e atacar locais de alto consumo sonoro B2B.
*   **ALVOS PRINCIPAIS:** `"loja de instrumentos musicais"`, `"distribuidor som automotivo"`, `"acústica e som"`.

### 🛒 Varejistas de Médio Porte (Tier 3)
*   **FOCO:** Redes de médio porte e comércio regional de giro para produtos de curva B/C, eletroportáteis, brinquedos e eletrônicos de consumo.
*   **ALVOS PRINCIPAIS:** `"supermercado"`, `"hipermercado"`, `"loja de móveis e eletro"`, `"loja de departamentos"`, `"atacarejo"`, `"loja de utilidades domésticas"`, `"eletromóveis"`.
*   **O QUE FOI CORTADO:** Grandes redes nacionais (Magazine Luiza, Casas Bahia, Lojas Cem, Pernambucanas, Marabraz, Gazin, Colombo, Novo Mundo, Assaí, Atacadão Carrefour, Sam's Club, Pão de Açúcar) e serviços puros/comércios sem relevância (drogarias, oficinas, postos, restaurantes).
*   **FIT SCORE TIER 3:**
    *   **Tier 1 (+80):** Supermercados, Hipermercados, Atacarejos e Redes Alimentícias regionais.
    *   **Tier 2 (+50):** Móveis e Eletro, Eletromóveis e Lojas de Departamentos.
    *   **Tier 3 (+30):** Utilidades Domésticas, Bazar e Variedades.

---
*Documento gerado como base analítica para garantia do funil B2B do motor de prospecção ativa do CRM Multilaser.*
