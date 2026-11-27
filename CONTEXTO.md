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
4. Limites no infinito — **FEITA**
5. L'Hôpital, ∞−∞, 0·∞ e indeterminações com potência — **FEITA**
6. API (rota `/limite`) — **FEITA**
7. Página (formulário e passo a passo) — **FEITA**
8. Gráfico — **FEITA**
9. Testes de todos os tipos e revisão das explicações — **FEITA**
10. Entrada por imagem (colar/enviar uma foto da conta; extração da função e
    do ponto via API de visão do Gemini) — **FEITA** (branch
    `feature/etapa-10-entrada-imagem`, ainda sem PR; ver seção 9)

## 5. Estado atual

Confira sempre com `git log --oneline --graph --all`, `git status` e `pytest`.

Repositório: `git@github.com:MayzaBernardi/calculadora-limites.git` (SSH já
autenticado).

Situação das branches no GitHub:

- `main`: base do projeto, Etapas 1 a 4 já mescladas, e agentes do Claude
  Code (PRs #1 a #10). A Etapa 2 entrou um commit por técnica: `650f08e`
  identificação de formas indeterminadas, `21fa078` fatoração, `1e930f0`
  racionalização pelo conjugado e `973988b` limites fundamentais, mesclados
  via PR #5 (`89e3e31`). A Etapa 3 (`942d774`, limites laterais, k/0 e
  domínio de um lado só) foi mesclada via PR #7 (`7e420f4`). A Etapa 4 entrou
  em dois PRs: o primeiro commit (termo dominante de polinômios, `277c346`)
  via PR #9 (`55413b4`); os outros dois (`eeeff73` divisão pela maior
  potência e `027c519` função limitada sobre infinito) via PR #10 (`e416913`).
  Etapa 4 completa e mesclada. Da Etapa 5, já estão na `main` o L'Hôpital
  (`a8e41ed`) via PR #12 (`529b26b`), e depois `80b93a4` (corrige um bug de
  LaTeX da fatoração, Etapa 2), `6673725` ∞−∞ por denominador comum,
  `bf04871` ∞−∞ por conjugado e `d89beb2` 0·∞ por produto como quociente,
  via PR #13 (`1454310`).
- `feature/etapa-2-zero-sobre-zero`, `feature/etapa-3-laterais-k-sobre-zero` e
  `feature/etapa-4-limites-no-infinito`: já mescladas na `main`; só falta
  apagar os remotos quando quiserem.
- `feature/etapa-6-api` e `feature/etapa-7-pagina`: Etapas 5, 6 e 7 já
  mescladas na `main` via PRs #14, #15 e #16. A dona do projeto abriu a
  página de verdade (backend + `http.server`) depois da Etapa 8 e seguiu
  sem reportar problema visual.
- `feature/etapa-8-grafico` e `feature/etapa-9-testes-revisao`: Etapas 8 e 9
  completas e **já mescladas na `main` via PR #17** (commit de merge
  `655e487`). Todas as 9 etapas do projeto original estão, portanto,
  completas e na `main`. Só falta apagar os remotos dessas branches, se
  quiserem.
- `feature/melhoria-visual-interativa`: redesign visual do frontend (tema
  claro/escuro, animações, microinterações, cartões com sombra), mais a
  correção do indicador de carregando que ficava visível antes de calcular
  (`.carregando:not([hidden])`, achada testando a página de verdade). PR
  #18, **já mesclado na `main`** (commit de merge `3bd278d`). Só falta
  apagar o remoto, se quiserem.
- `feature/etapa-10-entrada-imagem`: Etapa 10 completa (backend e
  frontend — detalhes na seção 9), push feito, **sem PR aberto ainda**
  (decisão pendente).
- `feature/teclado-simbolos`: teclado de símbolos na página de texto, fora
  do plano original (detalhes na seção 9), push feito, **sem PR aberto
  ainda** (decisão pendente).

Não presuma: rode `git fetch` e confira `git log --oneline --graph --all`.

Ambiente: `backend/.venv` já existe e é ignorado pelo git. Se faltar, rode
`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` dentro de
`backend/` (no Ubuntu pode ser preciso `apt install python3.12-venv`). Requer
também `GEMINI_API_KEY` em `backend/.env` para a rota `/limite/imagem`
funcionar de verdade (opcional para rodar os testes — a suíte nunca depende
da chave real, ver seção 9). Testes: `cd backend && .venv/bin/pytest -q`
(hoje: 588 passando — 582 do motor/API original + 6 de `/limite/imagem` —,
em cerca de 2-3 min; cada limite roda em processo filho e alguns testes
esperam o timeout de 3 s).

**Código em `backend/app/motor/` (fim da Etapa 9):**

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
- `formas.py`
  - `identificar_forma(expr, ponto)` devolve `"0/0"`, `"oo/oo"`, `"k/0"`,
    `"oo/0"`, `"0*oo"`, `"oo-oo"`, `"1^oo"`, `"0^0"`, `"oo^0"` ou `None`.
    Em ponto finito a forma precisa ser a mesma pelos dois lados (lados onde a
    função existe); se diferem, `None` (a Etapa 3 trata laterais).
  - `limite_da_parte`, `definida_no_lado` e `lados_definidos` (amostra numérica
    em float, dentro de `executar_com_timeout`; se não der para avaliar a
    tempo o lado é "não confiável" e a forma vira `None`).
  - `_forma_no_lado` (Etapa 5): testa a potência (`_forma_potencia`) *antes*
    de `sp.fraction`. Correção de um bug achado na revisão da Etapa 5: com
    sinal negativo explícito no expoente (ex.: `(1+1/x)^(-x)`), o SymPy
    reescreve a potência como `1/base**x`, e testar o quociente primeiro
    fazia a forma nunca ser reconhecida como `1^oo`/`0^0`/`oo^0` (o motor
    caía num passo que afirmava, errado, que "não há indeterminação"). Cai no
    quociente normalmente (`k/0` em `1/x`, por exemplo) quando não é uma das
    três formas de potência.
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
  - `termo_dominante` (Etapa 4): polinômio puro (`is_polynomial(x)`) com
    x → ±∞; o termo de maior grau decide o sinal do infinito (coeficiente
    líder, paridade do grau e sentido do infinito).
  - `divisao_maior_potencia` (Etapa 4): função racional (numerador e
    denominador polinomiais, os dois dependendo de x) com x → ±∞, forma
    ∞/∞; divide os dois pela maior potência do denominador. Três casos:
    grau do numerador menor (limite 0), igual (razão dos coeficientes
    líderes) ou maior (±∞, mesmo raciocínio de sinal do `termo_dominante`,
    reimplementado à parte). Exclui de propósito `k/polinômio` e
    `polinômio/k` (numerador ou denominador sem x) — não é ∞/∞ de verdade.
  - `limitada_sobre_infinito` (Etapa 4; generalizada na Etapa 9): `g(x)/h(x)`
    com x → ±∞, `h(x)` → ±∞ e `g(x)` limitada perto do infinito (reconhece,
    via `intervalo_limitado`: números, sen/cos de qualquer argumento, soma
    de partes limitadas, e produto de qualquer número de fatores com
    intervalo conhecido, inclusive vários dependendo de x, como
    `sen(x)·cos(x)` — a Etapa 9 generalizou isso; antes só aceitava no
    máximo um fator dependendo de x, e produtos como esse caíam, errado, no
    passo "Sem indeterminação"). Quando só uma parte do numerador é
    limitada (ex. `x·cos(x)`: `cos(x)` é, `x` não), `_separar_parte_limitada`
    move o resto para o denominador (dividir os dois pelo mesmo fator não
    muda a fração) antes de tentar de novo; recua sem concluir se o novo
    denominador não tender a ±∞ (nunca com valor errado). Conclui por
    confronto em valor absoluto (`|g/h| <= C/|h| -> 0`) que o limite é
    sempre 0. Não trata o caso em que é o denominador que oscila
    (`x/sen(x)`, sem limite).
  - `aplicar_lhopital` (Etapa 5): 0/0 ou ∞/∞ com fração explícita
    (`sp.fraction`); deriva numerador e denominador separadamente (nunca a
    fração inteira). Último recurso para 0/0 (depois de fatoração,
    racionalização e fundamentais); primeira tentativa para ∞/∞ (que as
    outras não cobrem). Devolve `None` se não há fração, se é grande demais,
    ou se derivar não mudou nada.
  - `denominador_comum` e `racionalizar_oo_menos_oo` (Etapa 5, ∞−∞): o
    primeiro junta soma/diferença de termos com `sp.together` (qualquer
    `Add`, desde que algum termo tenha fração); o segundo é só para soma de
    exatamente 2 termos com raiz quadrada e sem fração nenhuma (ex.:
    `sqrt(x²+x) - x`), multiplica e divide pelo conjugado. Tentados nessa
    ordem; o resolvedor tenta os dois antes de desistir.
  - `produto_como_quociente` (Etapa 5, 0·∞): só para produto de exatamente 2
    fatores; reescreve `fator_zero · fator_infinito` como
    `fator_zero / (1/fator_infinito)` (duas camadas de `evaluate=False` para
    o SymPy não desfazer a divisão). Produtos de 3+ fatores ficam fora de
    escopo (fallback de laterais, nunca valor errado) — é a limitação que
    afeta, por exemplo, `2*x*sen(1/x)` fora do contexto de potências (veja
    `potencia_para_exponencial` abaixo, que contorna isso só para o caso de
    potência, separando o coeficiente antes).
  - `potencia_para_exponencial` (Etapa 5, última técnica): 1^∞, 0^0 ou ∞^0;
    reescreve `f(x)^g(x)` como `e^(g(x)·ln(f(x)))` (base positiva garantida
    por quem já identificou a forma). Separa do expoente uma eventual
    constante numérica (`expoente.as_coeff_Mul()`) antes de montar o produto
    `resto · ln(f)`, para que ele continue com exatamente 2 fatores (o que
    `produto_como_quociente` exige); a constante volta a multiplicar o
    expoente da exponencial no final (cobre, por exemplo,
    `(1+1/x)^(2x) → e²`, que sem isso ficaria sem conclusão pela limitação
    acima).
- `passos.py`
  - `Passo(titulo, explicacao, latex)`; helpers `tex`, `tex_ordenado`,
    `texto_ponto`, `limite_tex` (soma entra entre parênteses) e
    `substituicao_tex`.
  - Construtores de passo de cada técnica, mais `passo_forma_indeterminada`,
    `passo_resultado` e `passo_tecnica_sem_conclusao`. `passo_lhopital`,
    `passo_denominador_comum`, `passo_racionalizacao_infinita`,
    `passo_produto_como_quociente` e `passo_potencia_exponencial` (Etapa 5)
    seguem o mesmo padrão: explicação em português da técnica, LaTeX
    mostrando a reescrita.
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
    forma e, se for 0/0, tenta fatoração, racionalização, limites
    fundamentais e por fim L'Hôpital, nessa ordem; se for ∞/∞, L'Hôpital
    direto; se for ∞−∞, denominador comum ou conjugado; se for 0·∞, produto
    como quociente; se for 1^∞/0^0/∞^0, potência como exponencial (todas as
    técnicas da Etapa 5), com `PROFUNDIDADE_MAXIMA = 5`. `_continuar`
    resolve a expressão transformada e confere com `conferir_com_sympy`; tem
    os parâmetros opcionais `multiplicador` (fator de um limite fundamental,
    ou a constante tirada do expoente numa potência) e `exponencial` (Etapa
    5: o valor final é `e^(multiplicador · valor_da_subexpressão)`, em vez
    de `multiplicador · valor`). Se a técnica não conclui ou diverge do
    SymPy, descarta os passos dela e registra um passo honesto ("Não
    conseguimos concluir" / "Conferência não coincidiu"), com
    `resolvido=False`. Em ponto finito, se a conferência não confirma
    (`validado is None`), a técnica também não afirma o valor; só a
    substituição direta pura vale sem conferência. Decimais viram racionais.
    Correção da Etapa 9: antes de anexar `sub.passos[1:]` (os passos da
    subexpressão resolvida recursivamente), `_continuar` descarta o último
    se for "Resultado" — sem isso, toda cadeia de 2+ níveis de técnica
    (qualquer potência indeterminada, por exemplo) empilhava um "Resultado"
    por nível, repetindo o mesmo passo (ou mostrando valores intermediários
    em sequência sem explicação).

Testes em `backend/testes/test_motor.py`; `pytest.ini` já configura
`pythonpath = .`.

Limitações conhecidas ao fim da Etapa 9 (revisão final): a derivação passo a
passo de 0·∞, 0^0, ∞−∞ e potências (que ficavam para a Etapa 5) está feita.
Segue valendo: funções que oscilam sem numerador algum reconhecido como
limitado (`sen(1/x)` em 0; `x/sen(x)` em ±∞, onde é o denominador que
oscila, nunca o numerador) terminam sem conclusão — de propósito, nunca com
valor errado; `produto_como_quociente` só aceita produto de exatamente 2
fatores (um 0·∞ genérico com 3+ fatores, fora do caso de potência com
coeficiente que `potencia_para_exponencial` já contorna, cai no fallback de
laterais); `racionalizar_oo_menos_oo` só aceita soma de exatamente 2 termos
com raiz (ex. `sqrt(x²+x) - x - 1` em `+∞` não conclui). Já não vale mais
dizer que `sen(x)*cos(x)/x` em ±∞ (e casos parecidos, como
`x*cos(x)/(x²+1)`) terminam sem conclusão: a revisão final (Etapa 9) achou
que esses casos caíam, antes, num passo "Sem indeterminação" com
justificativa matematicamente falsa (a expressão oscila; o valor 0 vem do
teorema do confronto, não de "ausência de indeterminação") — corrigido
generalizando `intervalo_limitado` e `limitada_sobre_infinito` (ver acima).
A mesma revisão achou e corrigiu passos "Resultado" duplicados em cadeias
de 2 ou mais níveis de recursão entre técnicas (ver nota em `_continuar`,
acima).

Lacunas novas, achadas só nessa revisão cruzada (e não antes, porque cada
revisão por etapa olhava uma técnica isolada por vez), documentadas e não
corrigidas por serem pontuais: raiz de índice ímpar de base negativa (ex.
`x^(1/3)` em `0` ou em `-8`) é tratada como fora do domínio real pela
amostragem numérica de `definida_no_lado`, mesmo quando `sp.limit` dela
mesma (o oráculo que o motor usa para conferir) aceita um valor real nesse
ramo — o motor nunca afirma errado (fica "de um lado só" ou `resolvido=False`),
mas a convenção usual de Cálculo (raiz ímpar definida em todo ℝ) não é
seguida; `piso(x)/x` em `+∞` não conclui (seria o confronto clássico
`(x-1)/x ≤ piso(x)/x ≤ x/x`, limite 1, mas `piso(x)` não é reconhecida como
limitada, corretamente, já que não é — só não há técnica de confronto para
numerador ilimitado mas "preso" perto do denominador); radicais aninhados
em que o conjugado ainda sobra com raiz (ex.
`sqrt(x+sqrt(x)) - sqrt(x)` em `+∞`, valor 1/2) não concluem, pelo mesmo
motivo do `racionalizar_oo_menos_oo` acima.

A Etapa 3 foi feita sem os agentes (indisponíveis na sessão); a revisão foi
uma varredura de 1057 limites contra o `sp.limit`, com 0 divergências. As
Etapas 4, 5 e 9 usaram os agentes (`motor-limites` e `revisor-matematico`);
a revisão de cada técnica (e, na Etapa 9, a varredura final cruzando todas)
incluiu varreduras de centenas de casos aleatórios contra `sp.limit`, 0
divergências numéricas encontradas em nenhuma delas (a da Etapa 4 achou um
bug real de LaTeX — parênteses faltando na divisão pela maior potência —,
corrigido antes do commit; a da Etapa 5, na técnica de potências, achou um
bug real de identificação de forma — veja `_forma_no_lado` acima —, também
corrigido antes do commit; a da Etapa 9 achou os dois problemas de clareza
pedagógica descritos acima, ambos corrigidos). Limites fundamentais (Etapa
2) não tratam: deslocamento por π (mas `sen(pi*x)/(x-1)` em `1`, que citava
isso aqui, já resolve certo por L'Hôpital desde a Etapa 5, valor `-π`), nem
potências de sen diferentes de 2. O teste de domínio (`definida_no_lado`) é
numérico, com amostra a 1e-6 do ponto, e roda em processo com timeout de
3 s; funções que oscilam muito perto do ponto podem ser classificadas
errado ou ficar sem conclusão (de propósito, nunca com valor errado).

**Código da API (`backend/app/`, fim da Etapa 8):**

- `main.py`: instancia o `FastAPI`, CORS (`allow_origins` com portas comuns de
  dev local — 5500, 5173, 8080, 3000 —, configurável por
  `ORIGENS_PERMITIDAS` no ambiente; `allow_credentials=False` de propósito,
  já que o projeto não usa cookies/autenticação) e inclui `rotas/limite.py`.
  Handlers de exceção garantem que toda resposta de erro (400/422/500) tem
  sempre o formato `{"erro": "mensagem em português"}`, nunca stack trace.
- `rotas/limite.py`: `POST /limite`. Chama `ler_funcao`/`ler_ponto` (erros de
  entrada viram 400 com a mensagem do `ErroEntrada`) e depois `resolver()`.
  A chamada completa a `resolver()` roda com um teto de 10s
  (`_resolver_com_timeout`, cópia local de `executar_com_timeout` com
  `daemon=False` — **nota para quem tocar em `seguro.py`:** não dá para
  reaproveitar a função original porque ela usa processo daemon, e
  `resolver()` já cria processos filhos por dentro, via `limite_seguro`; um
  daemon não pode ter filhos. Se quiserem eliminar essa duplicação, a
  correção é um parâmetro `daemon: bool = True` em
  `seguro.py::executar_com_timeout`). Monta a resposta a partir do
  `Resultado` do motor; valores em texto usam `texto_ponto` do motor (com um
  ajuste só na API para a constante `E` do SymPy aparecer como `e`
  minúsculo).
- `modelos/schemas.py`: o contrato (Pydantic). `EntradaLimite(funcao, ponto)`
  (strings). `RespostaLimite`: `entrada` (eco), `resolvido` (o motor
  concluiu?), `existe` (None se `resolvido=False`), `resultado`
  (`{texto, latex}` ou `None`), `laterais` (`None` se x → ±∞; senão
  `{esquerda, direita}`, cada um `{texto, latex}` ou `None` se a função não
  existe nesse lado), `passos` (lista de `{titulo, explicacao, latex}`,
  sempre com pelo menos 1), `grafico.pontos` (lista de `{x, y}`, `y: None`
  fora do domínio real), `ponto_grafico` (Etapa 8: o x pedido como `float`,
  `None` se infinito) e `valor_grafico` (Etapa 8: o y do resultado como
  `float`, `None` se não resolvido, não existe ou não for real finito — o
  frontend não dá para confiar em `resultado.texto`/`latex` para plotar,
  que pode ser `"e"`, `"π"`, `"4/3"`; por isso os dois já vêm como número
  pronto, calculados em `rotas/limite.py`). Erros sempre `{"erro": "..."}`
  (`RespostaErro`).
- `grafico/pontos.py`: amostra `f(x)` com `sp.lambdify` (NumPy) — ponto
  finito: janela `[ponto−5, ponto+5]`; x → +∞: `[−10, 30]`; x → −∞:
  `[−30, 10]`; 201 pontos (ímpar de propósito, para o próprio ponto cair
  exatamente na malha em ponto finito). Avaliação do lote inteiro protegida
  por um único `executar_com_timeout` (5s); NaN, complexo (fora de uma
  tolerância) e não finito viram `y=None`.

**Código da página (`frontend/`, fim da Etapa 8):**

- `index.html`: formulário com `campo-funcao` e `campo-ponto` (`novalidate`
  de propósito — a validação de campo vazio/inválido é só da API, que já
  devolve mensagem em português, em vez da bolha nativa do navegador),
  `indicador-carregando`, `area-erro` (`role="alert"`) e `area-resultado`
  (`aria-live="polite"`). KaTeX 0.16.9 via CDN (jsdelivr), com `integrity`
  (SRI) travado — recalculado e confirmado pela orquestradora, não só
  copiado do agente.
- `js/api.js`: `calcularLimite(funcao, ponto)` chama `POST /limite` (URL
  numa única constante `API_URL`, hoje `http://127.0.0.1:8000`) e lança
  `Error` com mensagem em português pronta para exibir — tanto para erro da
  API (lê `corpo.erro`) quanto para falha de rede (backend fora do ar).
- `js/passos.js`: trata os 3 estados do contrato
  (`resolvido=false` → "Não conseguimos concluir este limite";
  `existe=false` → "O limite não existe"; `existe=true` → mostra
  `resultado.latex`), a seção de laterais (omitida se `laterais` for
  `null`, isto é, ponto infinito; cada lado "Não definido nesse lado." se
  vier `null`) e a lista de passos, cada fórmula via
  `katex.render(latex, elemento, {throwOnError: false})`. Todo texto da API
  entra com `textContent` (nunca `innerHTML`) — só o `latex` de cada item
  chega ao KaTeX. Chama `renderizarGrafico` (abaixo) depois do bloco de
  resultado e antes dos passos.
- `js/grafico.js` (Etapa 8): `renderizarGrafico(resposta)` desenha
  `grafico.pontos` com Chart.js (4.4.9, CDN, `integrity` travado e
  recalculado pela orquestradora) como linha (`pointRadius: 0`,
  `spanGaps: false` — quebra a linha nos `y: null`, não liga os dois lados
  de uma assíntota ou furo). Só desenha o ponto destacado (segundo
  dataset, sem linha, raio maior, cor de contraste) quando `ponto_grafico`
  **e** `valor_grafico` vêm os dois não nulos — é a única combinação em
  que há um `(x, y)` de verdade para marcar; em qualquer outro caso (ponto
  infinito, limite que não existe ou não resolvido), mostra só a curva.
  Guarda a instância do `Chart` num módulo e chama `.destroy()` antes de
  desenhar de novo (recálculo na mesma página). Só lê números da resposta
  (nunca `innerHTML`/texto livre).
- Verificado (pela orquestradora, não só pelos agentes): os dois
  servidores no ar (`cd backend && .venv/bin/uvicorn app.main:app --port
  8000` e `cd frontend && python3 -m http.server 5500`, porta liberada no
  CORS) e chamadas reais via curl reproduzindo o `fetch` do frontend, para
  os 5 estados de resposta (existe, não existe, ponto infinito, não
  resolvido, entrada inválida), campo vazio, e a lógica de quando desenhar
  o marcador do gráfico (com e sem `ponto_grafico`/`valor_grafico`) — tudo
  bateu com o que o JS trata. Hashes SRI do KaTeX e do Chart.js
  recalculados com `openssl dgst -sha384` e conferidos contra o HTML.
  **Não verificado: a renderização visual de verdade** (CSS aplicado,
  KaTeX e Chart.js desenhando de fato na tela, responsividade) — nenhuma
  sessão até agora (nem os agentes `frontend-web`, nem a orquestradora)
  teve uma ferramenta de navegador disponível. Quem continuar deveria
  abrir a página de verdade antes de considerar as Etapas 7 e 8
  definitivamente fechadas.

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

**Todas as 9 etapas do projeto original estão completas e mescladas na
`main`** (PR #17 fechou a Etapa 9; confirme com
`git log --oneline --graph --all`). Testes do backend passando (582,
`cd backend && .venv/bin/pytest -q`). Pendências pequenas, sem urgência:

- Se quiserem, apagar as branches remotas já mescladas (Etapas 2 a 9).
- Qualquer lacuna documentada na seção 5 ("Limitações conhecidas") pode virar
  trabalho futuro, mas nenhuma delas afeta a correção do que já está pronto
  (o motor nunca afirma um valor errado; só fica honesto "sem concluir" nos
  casos fora de escopo).

Depois do fim da Etapa 9, a dona do projeto pediu dois pontos extras, fora do
plano original. Os dois estão implementados e testados; falta só decidir
sobre os PRs.

**1. Melhoria visual do frontend — concluída e já mesclada.** Tema
claro/escuro, animações, microinterações, cartões com sombra. PR #18,
mesclado na `main` (commit de merge `3bd278d`), incluindo a correção do
indicador de carregando que ficava visível antes de calcular
(`.carregando:not([hidden])`, achada testando a página de verdade).

**2. Etapa 10 — entrada por imagem (concluída, sem PR ainda).** Branch
`feature/etapa-10-entrada-imagem`, criada a partir da `main` (antes do PR
#18) e depois atualizada com `git merge main` para já incluir o redesign
visual — dois commits:

- `744eb93` (backend, agente `api-backend`): rota nova `POST /limite/imagem`
  (multipart, campo `imagem`, até 5 MB, PNG/JPEG/WEBP). `app/visao/gemini.py`
  chama o Gemini (SDK `google-genai`, modelo `gemini-3.6-flash` — escolhido
  testando de verdade com a chave: `gemini-3.8-flash` deu 503 de sobrecarga,
  `gemini-2.5-flash`/`2.0-flash` estão desativados para essa chave) com
  saída estruturada (`response_schema`) pedindo JSON `{funcao, ponto}` na
  sintaxe que `entrada.py` já aceita. Cliente do Gemini só é criado dentro
  da função (nunca no nível do módulo), para a API e os testes
  funcionarem sem `GEMINI_API_KEY` configurada; sem a chave, a rota devolve
  500 em português sem derrubar o resto da API. `app/rotas/limite.py` ganhou
  `montar_resposta()` (extraída de `calcular_limite`), reaproveitada pelas
  duas rotas a partir do ponto em que função e ponto já são `sp.Expr` — o
  campo `entrada` da resposta ecoa o que foi reconhecido na imagem, não um
  texto fixo. `main.py` chama `load_dotenv()` no início (caminho fixo,
  não quebra se `backend/.env` não existir). `backend/.env.example` documenta
  a variável (sem a chave de verdade). 6 testes novos em `test_api.py`,
  todos com `monkeypatch` na extração (nenhum depende de rede/chave real).
  588 testes passando no total.
- `2c67b37` (frontend, agente `frontend-web`): cartão novo "Calcular a
  partir de uma foto", abaixo do formulário de texto (que não mudou nada).
  Três jeitos de dar a imagem: `input[type=file]` nativo, colar com Ctrl+V
  (listener no `document`) e arrastar-e-soltar (extra). Pré-visualização
  antes de calcular, com botão de remover e outro, separado e visualmente
  diferente do "Calcular" de texto, para "Calcular pela imagem". `js/api.js`
  ganhou `calcularLimitePorImagem()` ao lado de `calcularLimite` (intocada);
  `js/passos.js` ganhou um parâmetro opcional em `exibirResposta()` que, só
  no fluxo de imagem, mostra "Reconhecemos na imagem: f(x) = ..., x → ..."
  antes do resultado (sempre `textContent`, nunca `innerHTML`); `js/imagem.js`
  (novo) cuida de seleção/validação no cliente/pré-visualização, sem
  duplicar renderização. `definirCarregando` (texto) e a lógica equivalente
  do fluxo de imagem se desabilitam mutuamente, para não disparar os dois
  cálculos ao mesmo tempo.

Decisão de segurança já aplicada (não é negociável): a chamada ao Gemini
roda só no backend, chave em variável de ambiente, nunca exposta ao
frontend.

Achado testando a página de verdade (commit `7c705d3`): digitar uma conta
sem parênteses em volta do numerador/denominador (ex.
`sen x + sen 3x + sen 6x / x + sen x`) dá um valor diferente do esperado —
não por bug do motor (a precedência padrão, divisão antes de soma, é a
correta e bate com `sympy.limit` puro), mas porque essa notação de uma
linha só não representa a fração de duas camadas que a pessoa tinha em
mente. Isso é um risco real para a Etapa 10: se a foto mostra uma fração de
verdade (traço horizontal) com mais de um termo em cima e/ou embaixo, o
Gemini precisa saber que tem que acrescentar parênteses ao achatar isso em
texto. O `PROMPT` em `app/visao/gemini.py` ganhou uma regra explícita sobre
isso, com um exemplo nesse exato formato — testado de novo com uma imagem
de fração desenhada com traço horizontal (PIL, fora do repo): o Gemini
passou a devolver `(sen(x)+sen(3x)+sen(6x))/(x+sen(x))`, resolvido certo
(valor 5, conferido com `sympy.limit`).

Verificação feita pela orquestradora (não só pelos agentes): 588 testes
(`cd backend && .venv/bin/pytest -q`); chamada real de ponta a ponta com os
dois servidores no ar — imagens de teste geradas com PIL (fora do repo),
reconhecidas e resolvidas certo (`(x²-4)/(x-2)` em `2` → 4,
`(1-cos x)/x²` em `0` → 1/2, `(3x²+1)/(x²+5)` em `+∞` → 3); tipo de
arquivo inválido e imagem maior que 5 MB devolvendo 400; chave ausente
devolvendo 500 sem derrubar `/limite` de texto; réplica exata em Node da
chamada `fetch`+`FormData` que `js/api.js` faz, contra o backend real, para
confirmar que o nome do campo (`imagem`) e a ausência de `Content-Type`
manual (o navegador define o boundary do multipart sozinho) batem.

Falta: decidir sobre o PR de `feature/etapa-10-entrada-imagem` (perguntar
antes de abrir/mesclar, como sempre) e, se quiserem, apagar as branches
remotas já mescladas.

**3. Teclado de símbolos — concluído, sem PR ainda.** Branch
`feature/teclado-simbolos`, criada a partir da `main` já com o redesign
visual e a Etapa 10 mesclados. Dois commits:

- `938f78b`: primeira versão — painel escondido por padrão atrás de um
  botão "Mostrar teclado de símbolos" (disclosure acessível,
  aria-expanded/aria-controls), com botões para as funções que o motor
  aceita (sen, cos, tg, ln, raiz, arcsen, arccos, arctg, piso, teto),
  módulo com barras, parênteses, operadores, constantes/variável,
  dígitos, apagar e limpar. `js/teclado.js` (novo) rastreia qual dos
  dois campos (`campo-funcao`/`campo-ponto`) foi focado por último e
  insere ali, na posição real do cursor; botões de função envolvem uma
  seleção existente ou, sem seleção, inserem a forma vazia com o
  cursor já dentro dos parênteses/barras.
- `9b9269b`: redesenho como calculadora sempre visível (sem o
  disclosure de antes) — "bezel" escuro com os dois campos por cima e
  uma grade de teclas por baixo, com relevo. Reduz o conjunto de
  teclas em relação à primeira versão: saem sen/cos/tg/ln/arcsen/
  arccos/arctg/piso/teto e o "^" genérico (continuam dando para
  digitar à mão); entram x², √ (continua envolvendo seleção), π, e, ∞,
  dígitos, operadores e apagar/limpar, numa grade de calculadora.
  Acrescenta `marcarCampoAtivo`: destaque visual permanente (não só o
  anel de foco, que some ao clicar numa tecla) de qual campo vai
  receber a próxima tecla — corrige um bug relatado pela dona do
  projeto (clicar em "x tende a" e depois numa tecla pensando na
  função inseria no campo errado, sem aviso).

Achado testando a página de verdade: depois de editar os 3 arquivos
(`estilo.css`, `index.html`, `js/teclado.js`) repetidas vezes para o
redesenho, os cliques pararam de fazer efeito na aba já aberta da dona
do projeto — sintoma de cache do navegador (JS/HTML antigos
desencontrados), não bug do código. Confirmado testando com Chromium
de verdade (ver abaixo): hard refresh (Ctrl+Shift+R) resolveu.

Verificação do redesenho (`9b9269b`): pela primeira vez nesta branch
havia Chromium disponível no ambiente (via Playwright, já instalado em
cache). Testado de verdade, não só por leitura de código: simulação
com jsdom (clique via `dispatchEvent`, inserir "x" e depois "x²" dá
"x^2", destaque do campo ativo liga) e depois no Chromium real,
servido pelo `http.server` já no ar em `127.0.0.1:5500` —
`getComputedStyle` confirma texto branco visível sobre o bezel escuro
(sem `display:none`/`opacity:0`/sobreposição) e screenshot confere o
resultado batendo com o esperado.

Falta: decidir sobre o PR de `feature/teclado-simbolos` (perguntar
antes de abrir/mesclar, como sempre).
