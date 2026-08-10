# 🐉 HydraDAST
> **Plataforma de Pentest Autônomo com Aprendizado Semântico e por Reforço**

O HydraDAST é uma plataforma de Dynamic Application Security Testing (DAST) de última geração desenvolvida como Projeto de Conclusão de Curso (2026). O sistema rompe com a abordagem de "força bruta" dos fuzzers tradicionais, utilizando Inteligência Artificial para compreender o contexto das aplicações e otimizar a descoberta de vulnerabilidades.

## 📖 Visão Geral do Problema
As aplicações modernas possuem uma explosão de rotas e microserviços. Testar cada campo manualmente é impraticável, e ferramentas automatizadas comuns geram um volume insustentável de falsos positivos e carga desnecessária nos servidores. O HydraDAST surge para automatizar esse processo com a precisão de um especialista humano.

## 🧠 Arquitetura Técnica e Funcionamento
O projeto é dividido em cinco camadas inteligentes que funcionam de forma coordenada:

### 1. Web Scraping e Reconhecimento de Ativos
O sistema utiliza o Playwright para realizar uma varredura profunda e dinâmica na aplicação alvo. Diferente de scrapers estáticos, o HydraDAST renderiza o JavaScript da página, permitindo:
- Mapeamento de Shadow APIs: Identificação de endpoints de API que não estão explícitos no HTML, mas são acionados via chamadas assíncronas (AJAX/Fetch).
- Extração de Metadados: Além de capturar campos de entrada (<input>, <textarea>), o sistema coleta atributos como id, name, placeholder, label associado e o tipo de dado esperado.
- Modelagem com Pydantic: Os dados extraídos são convertidos em objetos estruturados, garantindo que a inteligência artificial processe informações limpas e normalizadas.
### 2. Reconhecimento Semântico (NPL)
Diferente de scanners comuns, o HydraDAST entende o que está lendo.
- NLP & Embeddings: Utilizamos o modelo MiniLM-L12-v2 para transformar nomes de campos (ex: user_id, login, username) em vetores matemáticos.
- Mapeamento de Contexto: Através de buscas de similaridade, a IA agrupa campos logicamente, permitindo que o sistema aplique estratégias de ataque específicas para "Identidade", "Busca" ou "Pagamento".
### 3. Motor de Eficácia 
Antes de disparar um ataque, o sistema avalia a probabilidade de sucesso.
- XGBoost Classifier: Um modelo de Gradient Boosting classifica os payloads de ataque contra o contexto do campo. Se um campo espera um JSON, o sistema descarta automaticamente ataques de formulários HTML simples, economizando processamento.
### 4. Aprendizado por Reforço 
O HydraDAST aprende em tempo real através de um ciclo de Feedback Loop.
- Agente RL: O sistema seleciona um ataque e observa a resposta do servidor.
- Recompensa: Respostas que indicam instabilidade (Erro 500), atrasos (Timing Attacks) ou vazamento de dados geram recompensas positivas, "ensinando" a IA a refinar sua estratégia para aquela aplicação específica.
### 5. Relatórios Inteligentes via LLM 
Os resultados técnicos brutos são processados pelo Gemini 1.5.
- Tradução Técnica: Converte logs de erro complexos em descrições claras.
- Remediação: Sugere trechos de código corrigidos e melhores práticas baseadas no OWASP Top 10.

## 🛠️ Tecnologias Principais
- **IA:** Python, XGBoost, Scikit-learn, Sentence-Transformers.
- **Web:** FastAPI, React.js, Playwright.
- **Dados:** PostgreSQL (Persistência de padrões de ataque).

## Instalação
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 -m playwright install chromium   # opcional: só para o crawler completo
```

> As dependências pesadas (Playwright, PostgreSQL/pgvector, sentence-transformers, XGBoost)
> são usadas pelo pipeline completo de IA. A **API de scan da demo** roda apenas com
> `fastapi`, `uvicorn` e `requests`, então sobe mesmo sem elas instaladas.

## ▶️ Como executar (demo integrada front + back)

O fluxo atual é uma fatia vertical funcional: o front dispara um scan real, acompanha
o progresso ao vivo e exibe o relatório com os resultados reais dos ataques HTTP.

### 1. Backend (API FastAPI)
A partir da pasta `backend/app`:
```bash
cd backend/app
python3 -m uvicorn api.api:app --reload --port 8000
```
- API em `http://localhost:8000`
- Documentação interativa (Swagger) em `http://localhost:8000/docs`

### 2. Frontend (React + Vite)
Em outro terminal, a partir de `frontend`:
```bash
cd frontend
npm install      # apenas na primeira vez
npm run dev
```
- Interface em `http://localhost:5173`
- Para apontar para outra URL de API, defina `VITE_API_URL` (ex.: `VITE_API_URL=http://localhost:8000 npm run dev`).

### 3. Rodar um scan
1. Acesse **Novo scan**, informe uma URL (ex.: `https://the-internet.herokuapp.com/login`).
2. Selecione os motores disponíveis (SQL Injection, XSS, Segurança de header).
3. Clique em **Iniciar pentest** — as etapas do *Progresso* atualizam ao vivo (polling).
4. Ao concluir, clique em **Abrir relatório** para ver as vulnerabilidades encontradas.
5. **Dashboard** e **Relatórios** listam os scans já executados (dados 100% reais da API).

### Endpoints principais
| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/scans` | Inicia um scan em background; retorna `id` e `status` |
| `GET`  | `/api/scans` | Lista os scans da sessão |
| `GET`  | `/api/scans/{id}` | Estado/relatório atual de um scan (usado no polling) |
| `GET`/`PUT` | `/api/config` | Configurações da aplicação |

> **Nota sobre o estado atual:** a API da demo executa os ataques HTTP de verdade e
> classifica as respostas com o `FeedbackService`. As camadas de IA (NLP semântico,
> motor de eficácia XGBoost e aprendizado por reforço) existem no código
> (`backend/app/services/`) mas ainda **não** estão no caminho do endpoint — essa é a
> próxima etapa de integração. O armazenamento dos scans é em memória (reinicia junto
> com o servidor).