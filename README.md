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
- **Frontend:** HTML, CSS, JavaScript, KaTeX e uma biblioteca de gráficos.

## Como rodar o backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

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
