# Calculadora de Limites com Passo a Passo

Trabalho de **Cálculo para Computação**. Aplicação web que calcula limites de
funções de uma variável (`x`) e mostra a resolução passo a passo, como seria
feita no papel, junto com o gráfico da função.

## Entrada

- a função, por exemplo `(x^2-4)/(x-2)`, `sen(3x)/x`, `(1+1/x)^x`;
- o valor para onde `x` tende: um número, `infinito` ou `-infinito`.

Os limites laterais são calculados automaticamente.

## Saída

- resultado do limite (ou a indicação de que ele não existe);
- limites pela esquerda e pela direita (quando o ponto é finito);
- passo a passo com título, explicação em português e fórmula em LaTeX;
- gráfico da função com o ponto do limite destacado.

## Tecnologias

- **Backend:** Python, SymPy, FastAPI, Uvicorn, Pydantic, NumPy, pytest.
- **Frontend:** HTML, CSS e JavaScript puros, KaTeX (fórmulas) e Chart.js
  (gráfico), os dois via CDN — sem build step.

## Como rodar o backend (motor e testes)

```bash
cd backend
python3 -m venv .venv            # se ainda não existir
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Como rodar a aplicação (API + página)

Dois processos, em terminais separados.

**1. API**, a partir de `backend/` (com o ambiente virtual já criado):

```bash
cd backend
.venv/bin/uvicorn app.main:app --port 8000
```

**2. Página**, a partir de `frontend/`:

```bash
cd frontend
python3 -m http.server 5500
```

Depois, abra `http://127.0.0.1:5500` no navegador. A porta 5500 (e também
5173, 8080 e 3000, em `localhost` ou `127.0.0.1`) já vem liberada no CORS da
API por padrão; para usar outra porta, defina a variável de ambiente
`ORIGENS_PERMITIDAS` (lista separada por vírgula) antes de iniciar o
`uvicorn`. Se a API rodar em outro host/porta, ajuste a constante
`API_URL` no topo de `frontend/js/api.js`.

## Etapas de desenvolvimento

Cada etapa é desenvolvida em uma branch `feature/...` própria.

1. Leitura da entrada e substituição direta
2. Indeterminação 0/0 (fatoração, racionalização, limites fundamentais)
3. Limites laterais, k/0 e domínio de um lado só
4. Limites no infinito
5. L'Hôpital, ∞ − ∞, 0 · ∞ e indeterminações com potência
6. API (rota `POST /limite`)
7. Página (formulário e passo a passo)
8. Gráfico
9. Testes de todos os tipos e revisão das explicações
