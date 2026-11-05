# Contexto: continuar a "Calculadora de Limites com Passo a Passo"

Documento de passagem para quem for continuar o projeto (pessoa ou sessão do
Claude Code). Leia tudo antes de agir. Responda sempre em português do Brasil.

## 1. Objetivo do projeto

Trabalho de faculdade (Cálculo para Computação). É uma aplicação web que
calcula limites de funções de uma variável (x) e mostra a resolução passo a
passo, como seria feita no papel, junto com o gráfico da função.

**Entrada:** só a função (ex.: `(x^2-4)/(x-2)`, `sen(3x)/x`, `(1+1/x)^x`) e o
valor para onde x tende (número, `infinito` ou `-infinito`). Não existe campo
de lado: os limites laterais são calculados automaticamente.

**Saída:** resultado do limite (ou "não existe"); limites pela esquerda e pela
direita (quando o ponto é finito); passo a passo com título, explicação em
português e fórmula em LaTeX; gráfico com o ponto do limite destacado.

**Tipos de limite a cobrir:**

- Substituição direta (função contínua).
- 0/0: limites fundamentais (sen u/u, (e^u−1)/u, ln(1+u)/u), fatoração,
  racionalização, L'Hôpital.
- ∞/∞: divisão pela maior potência, L'Hôpital.
- k/0: limite infinito, com análise do sinal.
- Laterais diferentes: o limite não existe (1/x, |x|/x, piso(x)).
- Funções definidas só de um lado (ln x, √x, x^x em 0): considerar só o lado
  do domínio.
- ∞−∞: denominador comum ou conjugado.
- 0·∞: reescrever como quociente.
- 1^∞, 0^0, ∞^0: usar lim f^g = e^(lim g·ln f).
- Polinômios com x → ±∞: termo dominante.

**Fluxo do motor:**

1. Tentar substituição direta.
2. Se o ponto é finito, calcular e comparar os limites laterais.
3. Identificar a forma indeterminada.
4. Aplicar a técnica adequada e registrar os passos.
5. Repetir na nova expressão (com limite de profundidade).
6. Conferir o resultado final com `sympy.limit`.

**Cuidados obrigatórios:**

- Tratar 0^0 como indeterminação (o SymPy considera 0^0 = 1).
- Tratar o `zoo` do SymPy como "limite não existe".
- Usar x como variável real (`Symbol("x", real=True)`).

## 2. Tecnologias

- **Backend (Python):** SymPy, FastAPI + Uvicorn, Pydantic, NumPy, pytest.
  CORS liberado para o frontend.
- **Frontend:** HTML, CSS e JavaScript puros, KaTeX para as fórmulas e uma
  biblioteca de gráficos (Chart.js, Plotly ou function-plot).
- **API:** `POST /limite`. Recebe a função e o valor de x. Devolve se o limite
  existe, o resultado (texto e LaTeX), os limites laterais, a lista de passos
  e os pontos do gráfico. Em caso de erro, devolve uma mensagem explicando o
  problema na entrada.

## 3. Estrutura de pastas (um único repositório)

```
calculadora-limites/
├── backend/
│   ├── app/
│   │   ├── main.py            (FastAPI, CORS, rotas)
│   │   ├── rotas/limite.py    (POST /limite)
│   │   ├── modelos/schemas.py (entrada e resposta, Pydantic)
│   │   ├── motor/
│   │   │   ├── entrada.py     (lê e valida função e x)
│   │   │   ├── resolvedor.py  (fluxo principal)
│   │   │   ├── laterais.py    (limites laterais e domínio)
│   │   │   ├── formas.py      (identifica a indeterminação)
│   │   │   ├── tecnicas.py    (fatoração, racionalização, L'Hôpital...)
│   │   │   └── passos.py      (monta cada passo)
│   │   └── grafico/pontos.py  (pontos x, y)
│   ├── testes/ (test_motor.py, test_api.py)
│   └── requirements.txt
├── frontend/ (index.html, estilo.css, js/api.js, js/passos.js, js/grafico.js)
├── .gitignore
└── README.md
```

## 4. Etapas de desenvolvimento

1. Leitura da entrada e substituição direta — **FEITA**
2. Indeterminação 0/0 (fatoração, racionalização, limites fundamentais)
3. Limites laterais, k/0 e domínio de um lado só
4. Limites no infinito
5. L'Hôpital, ∞−∞, 0·∞ e indeterminações com potência
6. API (rota `/limite`)
7. Página (formulário e passo a passo)
8. Gráfico
9. Testes de todos os tipos e revisão das explicações

## 5. Estado atual

Confira sempre com `git log --oneline --graph --all`, `git status` e `pytest`.

Repositório: `git@github.com:MayzaBernardi/calculadora-limites.git` (SSH já
autenticado). Raiz local: `/root/calculadoraLimites`.

Branches enviadas ao GitHub, encadeadas e **nada mesclado na `main`**:

- `main`: só o commit inicial (vazio).
- `feature/base-projeto`: README, `.gitignore` e `requirements.txt`.
- `feature/etapa-1-entrada-substituicao`: parte da anterior.
- `docs/contexto-projeto`: parte da anterior e só acrescenta este arquivo.
  **É daqui que a Etapa 2 deve sair.**

Ambiente: `backend/.venv` já existe e é ignorado pelo git. Se faltar, rode
`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` dentro de
`backend/` (no Ubuntu pode ser preciso `apt install python3.12-venv`). Testes:
`cd backend && .venv/bin/pytest -q` (hoje: 53 passando).

**Código existente em `backend/app/motor/`:**

- `entrada.py`
  - Define `x` (símbolo real) e `ErroEntrada` (a mensagem vai para o usuário).
  - `ler_funcao(texto)` aceita `sen`, `tg`, `ln`, `raiz`, `piso`, `|u|`, `^`,
    `e`, `pi` e multiplicação implícita (`2x`). Um whitelist de caracteres e
    um `global_dict` restrito protegem o `eval`.
  - `ler_ponto(texto)` devolve número, `oo` ou `-oo`; decimal vira `Rational`.
- `passos.py`
  - `Passo(titulo, explicacao, latex)` é um dataclass.
  - Helpers: `tex()`, `texto_ponto()`, `limite_tex()`, `substituicao_tex()`.
  - Construtores de passo: `passo_funcao_dada`, `passo_substituicao_direta`,
    `passo_substituicao_sem_resultado`.
- `resolvedor.py`
  - `Resultado(resolvido, existe, valor, passos)` é um dataclass.
  - `substituir(expr, ponto)` devolve `(valor, "")` ou `(None, motivo)`. Recusa
    funções com salto (floor, ceiling, sign), `0^0`, nan, zoo/oo e resultados
    não reais.
  - `resolver(expr, ponto)` é o fluxo principal. Hoje só faz a substituição
    direta e tem um comentário marcando onde entram as próximas etapas.

Testes em `backend/testes/test_motor.py`; `pytest.ini` já configura
`pythonpath = .`.

## 6. Como trabalhar (pedido explícito da dona do projeto)

- **Pouco de cada vez.** Uma etapa por vez, em incrementos pequenos.
- **Uma branch por feature**, no padrão `feature/etapa-N-nome-curto`, criada a
  partir da branch da etapa anterior (as etapas dependem umas das outras).
- **Commits pequenos, depois de cada incremento que funciona**, com os testes
  passando. Mensagem em português, no imperativo e com contexto, no estilo
  "Etapa 2: fatoração para 0/0". Termine a mensagem com a linha de co-autoria
  já usada nos commits anteriores (veja `git log -3 --format=%B`).
- Faça `git push -u origin <branch>` ao terminar cada etapa.
- **Não mescle na `main` nem faça force push sem pedirem.** Pergunte antes de
  qualquer ação irreversível.

## 7. Boas práticas de código

- **Escreva o teste junto com a funcionalidade**, em `testes/test_motor.py`,
  com `pytest.mark.parametrize` e casos de cada tipo. Inclua os casos de borda
  (0^0, zoo, domínio, laterais diferentes), não só os felizes.
- **Valide o resultado final com `sympy.limit`** (passo 6 do fluxo). Se o
  motor discordar do SymPy, investigue e não esconda a diferença.
- **Cada técnica gera passos pedagógicos.** Cada passo tem `titulo`,
  `explicacao` em português claro, como um professor explicaria, e `latex`
  correto. O foco é o aluno entender, e não só obter o número.
- **Separe responsabilidades** conforme a estrutura de pastas: `formas.py` só
  identifica a indeterminação, `tecnicas.py` só aplica técnicas, `passos.py`
  só monta passos, `resolvedor.py` orquestra.
- **Recursão com limite de profundidade**, para o motor nunca entrar em laço
  infinito (por exemplo, L'Hôpital repetido sem fim).
- **Nunca avalie texto do usuário diretamente.** Toda entrada passa por
  `entrada.py`. Não relaxe o whitelist nem o `global_dict`.
- **Erros de entrada** são `ErroEntrada` com mensagem em português, que a API
  devolve ao usuário. Não deixe stack trace vazar.
- **Segurança e robustez na API:** limite o tamanho da entrada, defina timeout
  para cálculos longos e libere CORS só para o necessário.
- **Mantenha o estilo do código existente:** nomes em português, docstrings
  curtas, poucos comentários e só quando explicam o "porquê".
- **Não deixe lixo no repositório:** `.venv`, `__pycache__` e `.env` ficam no
  `.gitignore`. Atualize o `README.md` quando algo mudar na forma de rodar.
- **Verifique antes de dizer que terminou:** rode os testes e, quando houver
  servidor ou página, rode-os de verdade. Reporte falhas com a saída real.

## 8. Limitação conhecida

`xsen(x)` (sem `*` nem espaço) é lido como `x*s*e*n` e dá erro de variável
desconhecida. Não é bug do motor; só vale melhorar a mensagem ou pré-processar
a entrada, se sobrar tempo.

## 9. Próximo passo

Confirme o estado do repositório (`git status`, `git log --oneline --graph
--all`, `pytest`). Depois crie `feature/etapa-2-zero-sobre-zero` a partir de
`docs/contexto-projeto` e comece pela identificação de formas indeterminadas
em `formas.py`, seguida das técnicas de 0/0 uma de cada vez. Faça um commit
por técnica.
