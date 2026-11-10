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
2. Indeterminação 0/0 (fatoração, racionalização, limites fundamentais) — **FEITA**
3. Limites laterais, k/0 e domínio de um lado só — **FEITA**
4. Limites no infinito
5. L'Hôpital, ∞−∞, 0·∞ e indeterminações com potência
6. API (rota `/limite`)
7. Página (formulário e passo a passo)
8. Gráfico
9. Testes de todos os tipos e revisão das explicações

## 5. Estado atual

Confira sempre com `git log --oneline --graph --all`, `git status` e `pytest`.

Repositório: `git@github.com:MayzaBernardi/calculadora-limites.git` (SSH já
autenticado).

Situação das branches no GitHub:

- `main`: base do projeto, Etapas 1, 2 e 3 já mescladas, e agentes do Claude
  Code (PRs #1 a #7). A Etapa 2 entrou um commit por técnica: `650f08e`
  identificação de formas indeterminadas, `21fa078` fatoração, `1e930f0`
  racionalização pelo conjugado e `973988b` limites fundamentais, mesclados
  via PR #5 (`89e3e31`). A Etapa 3 (`942d774`, limites laterais, k/0 e
  domínio de um lado só) foi mesclada via PR #7 (`7e420f4`).
- `feature/etapa-2-zero-sobre-zero` e `feature/etapa-3-laterais-k-sobre-zero`:
  já mescladas na `main`; só falta apagar os remotos quando quiserem.

Não presuma: rode `git fetch` e confira `git log --oneline --graph --all`.

Ambiente: `backend/.venv` já existe e é ignorado pelo git. Se faltar, rode
`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` dentro de
`backend/` (no Ubuntu pode ser preciso `apt install python3.12-venv`). Testes:
`cd backend && .venv/bin/pytest -q` (hoje: 311 passando, em cerca de 67 s;
cada limite roda em processo filho e alguns testes esperam o timeout de 3 s).

**Código em `backend/app/motor/` (fim da Etapa 3):**

- `entrada.py` (sem mudanças desde a Etapa 1)
  - Define `x` (símbolo real) e `ErroEntrada` (a mensagem vai para o usuário).
  - `ler_funcao(texto)` aceita `sen`, `tg`, `ln`, `raiz`, `piso`, `|u|`, `^`,
    `e`, `pi` e multiplicação implícita (`2x`). Whitelist de caracteres e
    `global_dict` restrito protegem o `eval`.
  - `ler_ponto(texto)` devolve número, `oo` ou `-oo`; decimal vira `Rational`.
- `seguro.py` (novo)
  - `limite_seguro(expr, ponto, direcao, tempo=3.0)`: todo `sp.limit` do motor
    passa por aqui. Roda em processo filho (fork) com timeout e devolve `None`
    se estourar (`executar_com_timeout` serve para outras contas). Antes, reescreve `a**x` (bug do SymPy em -oo) e
    `sqrt(quadrado perfeito)` como `Abs`. A API da Etapa 6 deve usá-lo.
- `formas.py` (novo)
  - `identificar_forma(expr, ponto)` devolve `"0/0"`, `"oo/oo"`, `"k/0"`,
    `"oo/0"`, `"0*oo"`, `"oo-oo"`, `"1^oo"`, `"0^0"`, `"oo^0"` ou `None`.
    Em ponto finito a forma precisa ser a mesma pelos dois lados (lados onde a
    função existe); se diferem, `None` (a Etapa 3 trata laterais).
  - `limite_da_parte`, `definida_no_lado` e `lados_definidos` (amostra numérica
    em float, dentro de `executar_com_timeout`; se não der para avaliar a
    tempo o lado é "não confiável" e a forma vira `None`).
- `laterais.py` (Etapa 3)
  - `calcular_laterais(expr, ponto)` devolve `Laterais(esquerda, direita)`,
    com `None` no lado onde a função não existe; devolve `None` se algum lado
    não pôde ser calculado de forma confiável (tempo, oscilação).
  - `concluir(laterais)`: um lado só vale esse lado; dois lados iguais dão o
    limite (inclusive ±∞); diferentes, o limite não existe.
  - `analisar_sinais`: no k/0, sinal do numerador e do denominador de cada
    lado (amostra numérica). Só explica se o sinal bate com o limite do SymPy.
- `tecnicas.py` (novo)
  - `fatorar_e_cancelar` (função racional, grau até 100).
  - `racionalizar` (conjugado de binômio com `sqrt`; raiz nos dois lados é
    feita em duas passadas pelo resolvedor).
  - `aplicar_limites_fundamentais` (sen u/u, tg u/u, (e^u-1)/u, ln(1+u)/u,
    (1-cos u)/u², (cos u-1)/u², sen²u/u², (a^u-1)/u, com u -> 0 por todos os
    lados em que a função existe).
- `passos.py`
  - `Passo(titulo, explicacao, latex)`; helpers `tex`, `tex_ordenado`,
    `texto_ponto`, `limite_tex` (soma entra entre parênteses) e
    `substituicao_tex`.
  - Construtores de passo de cada técnica, mais `passo_forma_indeterminada`,
    `passo_resultado` e `passo_tecnica_sem_conclusao`.
- `resolvedor.py`
  - `Resultado(resolvido, existe, valor, passos, validado, esquerda, direita)`;
    `validado` diz se o valor bateu com `sp.limit` (`None`: não conferido).
    `existe=False` com `valor=None` é "o limite não existe". `esquerda` e
    `direita` são os laterais em ponto finito (`None` no lado fora do domínio).
  - `substituir` também recusa o ponto isolado fora do domínio: `x^x` em -1
    dá -1 na conta, mas a função não é real em nenhum dos lados.
  - Quando nenhuma técnica de 0/0 conclui (ou a forma é k/0, oo/0, laterais
    diferentes, um lado só), `_por_laterais` calcula os laterais, registra os
    passos (laterais, análise de sinal, conclusão) e resolve. Divergência de
    uma técnica com o SymPy (`validado False`) não é escondida pelos laterais.
  - `resolver(expr, ponto, profundidade=0)`: substituição direta, identifica a
    forma e, se for 0/0, tenta fatoração, racionalização e limites
    fundamentais, nessa ordem (`PROFUNDIDADE_MAXIMA = 5`). `_continuar`
    resolve a expressão transformada e confere com `conferir_com_sympy`. Se a
    técnica não conclui ou diverge do SymPy, descarta os passos dela e
    registra um passo honesto ("Não conseguimos concluir" / "Conferência não
    coincidiu"), com `resolvido=False`. Em ponto finito, se a conferência não
    confirma (`validado is None`), a técnica também não afirma o valor; só a
    substituição direta pura vale sem conferência. Decimais viram racionais.

Testes em `backend/testes/test_motor.py`; `pytest.ini` já configura
`pythonpath = .`.

Limitações conhecidas ao fim da Etapa 3: pontos infinitos (Etapa 4) ainda não
são resolvidos. Na análise lateral o valor de cada lado vem do `sp.limit`
(via `limite_seguro`) e os passos explicam a comparação e o sinal; a
derivação passo a passo de 0·∞, 0^0 e afins (`x*ln(x)`, `x^x` em 0) fica para
a Etapa 5. Funções que oscilam (`sen(1/x)` em 0) terminam sem conclusão.
A Etapa 3 foi feita sem os agentes (indisponíveis na sessão); a revisão foi
uma varredura de 1057 limites contra o `sp.limit`, com 0 divergências.
Limites fundamentais não tratam: deslocamento por π (`sen(pi*x)/(x-1)` em 1),
`x*sen(1/x)`, `(sen x - x)/x^3` (precisa de L'Hôpital ou Taylor) e potências
de sen diferentes de 2. O teste de domínio (`definida_no_lado`) é numérico,
com amostra a 1e-6 do ponto, e roda em processo com timeout de 3 s; funções
que oscilam muito perto do ponto podem ser classificadas errado ou ficar sem
conclusão (de propósito, nunca com valor errado).

## 6. Como trabalhar (pedido explícito da dona do projeto)

- **Pouco de cada vez.** Uma etapa por vez, em incrementos pequenos.
- **Uma branch por feature**, no padrão `feature/etapa-N-nome-curto`, criada a
  partir da branch da etapa anterior (as etapas dependem umas das outras; se a anterior já foi mesclada, parta da `main` atualizada).
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

Etapa 3 mesclada na `main` (PR #7). Em andamento: `feature/etapa-4-limites-no-infinito`,
criada a partir da `main` atualizada: termo dominante de polinômios, divisão
pela maior potência em ∞/∞ e casos como `sen(x)/x` e `1/x` em ±∞.
