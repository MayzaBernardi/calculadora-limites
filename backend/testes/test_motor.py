import time

import pytest
import sympy as sp

from app.motor.entrada import ErroEntrada, ler_funcao, ler_ponto, x
from app.motor.formas import identificar_forma, lados_definidos, limite_da_parte
from app.motor.seguro import limite_seguro
from app.motor.passos import passo_forma_indeterminada
from app.motor.resolvedor import resolver


# ---------- leitura da função ----------

@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("(x^2-4)/(x-2)", (x**2 - 4) / (x - 2)),
        ("sen(3x)/x", sp.sin(3 * x) / x),
        ("(1+1/x)^x", (1 + 1 / x) ** x),
        ("|x|/x", sp.Abs(x) / x),
        ("piso(x)", sp.floor(x)),
        ("e^x", sp.exp(x)),
        ("ln(1+x)/x", sp.log(1 + x) / x),
        ("raiz(x)", sp.sqrt(x)),
        ("2x", 2 * x),
        ("x*sen(x)", x * sp.sin(x)),
    ],
)
def test_ler_funcao(texto, esperado):
    assert sp.simplify(ler_funcao(texto) - esperado) == 0


@pytest.mark.parametrize(
    "texto",
    ["", "   ", "x+y", "x+", "((x", "|x", "__import__('os')", "x.__class__", "x;1", "x" * 300],
)
def test_ler_funcao_invalida(texto):
    with pytest.raises(ErroEntrada):
        ler_funcao(texto)


# ---------- leitura do ponto ----------

@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("2", 2),
        ("0", 0),
        ("-3", -3),
        ("1/2", sp.Rational(1, 2)),
        ("-3.5", sp.Rational(-7, 2)),
        ("pi", sp.pi),
        ("infinito", sp.oo),
        ("+infinito", sp.oo),
        ("-infinito", -sp.oo),
        ("inf", sp.oo),
        ("-∞", -sp.oo),
    ],
)
def test_ler_ponto(texto, esperado):
    assert ler_ponto(texto) == esperado


@pytest.mark.parametrize("texto", ["", "x", "abc", "1+i", "1/0"])
def test_ler_ponto_invalido(texto):
    with pytest.raises(ErroEntrada):
        ler_ponto(texto)


# ---------- substituição direta ----------

def _resolver(funcao, ponto):
    return resolver(ler_funcao(funcao), ler_ponto(ponto))


def _iguais(a, b):
    return a == b or sp.simplify(a - b) == 0


def _confere_com_sympy(r, funcao, ponto):
    """Se o motor concluiu, o resultado bate com o sp.limit de cada lado (um
    lado fora do domínio real não conta). Nunca chama sp.limit sem timeout."""
    if not r.resolvido:
        return
    e, a = ler_funcao(funcao), ler_ponto(ponto)
    lados = lados_definidos(e, a)
    assert lados, "a função precisa existir de algum lado"
    laterais = [limite_seguro(e, a, d) for d in lados]
    laterais = [v for v in laterais if v is not None]
    assert laterais, "sem referência do SymPy"
    if r.existe:
        assert all(_iguais(v, r.valor) for v in laterais)
    else:
        assert len(laterais) == 2 and not _iguais(*laterais)
    for lado, valor in (("-", r.esquerda), ("+", r.direita)):
        if lado in lados and valor is not None:
            assert _iguais(limite_seguro(e, a, lado), valor)
        if lado not in lados:
            assert valor is None  # lado fora do domínio não tem lateral


@pytest.mark.parametrize(
    "funcao, ponto, esperado",
    [
        ("x^2+3x", "2", 10),
        ("3x-1", "-2", -7),
        ("cos(x)", "pi", -1),
        ("ln(x)", "1", 0),
        ("e^x", "0", 1),
        ("x^2", "-3.5", sp.Rational(49, 4)),
        ("sqrt(x)", "9", 3),
        ("|x|", "-4", 4),
    ],
)
def test_substituicao_direta(funcao, ponto, esperado):
    r = _resolver(funcao, ponto)
    assert r.resolvido and r.existe
    assert sp.simplify(r.valor - esperado) == 0
    assert [p.titulo for p in r.passos] == ["Limite a calcular", "Substituição direta"]


@pytest.mark.parametrize(
    "funcao, ponto",
    [
        ("x/sen(x)", "infinito"),  # denominador oscila: ainda não tratado
        ("sqrt(x)", "-1"),        # fora do domínio dos dois lados
        ("ln(x)", "-1"),          # fora do domínio dos dois lados
        ("sen(x)", "infinito"),   # sem denominador: só oscila, ainda não tratado
    ],
)
def test_substituicao_nao_resolve(funcao, ponto):
    r = _resolver(funcao, ponto)
    assert not r.resolvido
    assert r.valor is None


def test_passos_tem_latex_e_explicacao():
    r = _resolver("x^2+3x", "2")
    for passo in r.passos:
        assert passo.titulo and passo.explicacao and passo.latex
    assert "10" in r.passos[-1].latex


# ---------- identificação de formas indeterminadas ----------

@pytest.mark.parametrize(
    "funcao, ponto, esperada",
    [
        ("(x^2-4)/(x-2)", "2", "0/0"),
        ("sen(x)/x", "0", "0/0"),
        ("(e^x-1)/x", "0", "0/0"),
        ("(1-cos(x))/x^2", "0", "0/0"),
        ("1/x", "0", "k/0"),
        ("1/(x-1)^2", "1", "k/0"),
        ("x^x", "0", "0^0"),
        ("(1+1/x)^x", "infinito", "1^oo"),
        ("x^(1/x)", "infinito", "oo^0"),
        ("x*ln(x)", "0", "0*oo"),
        ("x-x^2", "infinito", "oo-oo"),
        ("1/x-1/x^2", "infinito", None),
        ("x^2/(x+1)", "infinito", "oo/oo"),
        ("(x^2)/(x)", "infinito", None),  # o SymPy já simplifica para x
        ("(3x^2+1)/(x^2-5)", "infinito", "oo/oo"),
        ("x+1", "2", None),
        ("x^2/(x+1)", "2", None),
        ("sen(x)", "0", None),
        ("|x|/x", "0", "0/0"),
        ("(1+x)^(1/x)", "0", "1^oo"),
        ("(sen(x)/x)^(1/x^2)", "0", "1^oo"),
        ("(sen(x)/x)^(1/x)", "0", "1^oo"),
        ("(x+1)^x", "0", None),
        ("x^(1/x)", "0", None),
        ("sqrt(x)/x", "0", "k/0"),   # só existe à direita
        ("ln(x)/x", "0", "oo/0"),
        ("piso(x)/x", "0", None),    # laterais dão formas diferentes
        ("1/x-1/x^2", "0", None),    # só à direita é oo-oo
        ("e^(1/x)*x", "0", None),    # esquerda e direita diferem
        ("sen(1/x)", "0", None),     # sem limite
        ("x*ln(x)", "infinito", None),
        ("2^x*x", "-infinito", "0*oo"),
        ("x*e^x", "-infinito", "0*oo"),
        ("(x^2-4)/(x-2)", "-infinito", "oo/oo"),
        ("x^2/(x+1)", "-infinito", "oo/oo"),
    ],
)
def test_identificar_forma(funcao, ponto, esperada):
    assert identificar_forma(ler_funcao(funcao), ler_ponto(ponto)) == esperada


def test_zero_sobre_zero_registra_passo_antes_dos_laterais():
    r = _resolver("sen(x)/x^2", "0")  # nenhuma técnica de 0/0 conclui
    assert [p.titulo for p in r.passos].index("Indeterminação 0/0") < [
        p.titulo for p in r.passos].index("Limites laterais")
    passo = next(p for p in r.passos if p.titulo == "Indeterminação 0/0")
    assert "simplificar" in passo.explicacao and passo.latex


def test_substituicao_direta_nao_registra_forma():
    r = _resolver("x+1", "2")
    assert r.resolvido
    assert all("Indeterminação" not in p.titulo for p in r.passos)


@pytest.mark.parametrize(
    "base, em_mais_oo, em_menos_oo",
    [
        (2, sp.oo, 0),
        (3, sp.oo, 0),
        (sp.Rational(1, 2), 0, sp.oo),
    ],
)
def test_limite_exponencial_numerica(base, em_mais_oo, em_menos_oo):
    """Fixa o comportamento correto (o SymPy 1.14 erra 2**x em -oo)."""
    assert limite_da_parte(base**x, sp.oo) == em_mais_oo
    assert limite_da_parte(base**x, -sp.oo) == em_menos_oo


@pytest.mark.parametrize(
    "forma, trecho_explicacao, trecho_latex",
    [
        ("0/0", "pode ser um número", r"\frac{0}{0}"),
        ("oo/oo", "∞/−∞", r"\frac{\infty}{\infty}"),
        ("k/0", "analisar o sinal", r"\frac{k}{0}"),
        ("oo/0", "numerador cresce", r"\frac{\infty}{0}"),
        ("0*oo", "quociente", r"0 \cdot \infty"),
        ("oo-oo", "juntar", r"\infty - \infty"),
        ("1^oo", "e^(g · ln f)", r"e^{g \ln f}"),
        ("0^0", "e^(g · ln f)", r"e^{g \ln f}"),
        ("oo^0", "e^(g · ln f)", r"e^{g \ln f}"),
    ],
)
def test_passo_de_cada_forma(forma, trecho_explicacao, trecho_latex):
    passo = passo_forma_indeterminada(x**2, sp.Integer(0), forma)
    assert trecho_explicacao in passo.explicacao
    assert trecho_latex in passo.latex
    assert passo.latex.startswith(r"\lim_{x \to 0}")


@pytest.mark.parametrize(
    "funcao, ponto",
    [("piso(x)/x", "0"), ("1/x-1/x^2", "0"), ("sen(1/x)", "0")],
)
def test_sem_forma_nao_registra_passo(funcao, ponto):
    r = _resolver(funcao, ponto)
    assert all("Indeterminação" not in p.titulo and p.titulo != "Divisão por zero"
               for p in r.passos)


@pytest.mark.parametrize(
    "funcao",
    ["(1+x)^(1/x)", "(sen(x)/x)^(1/x)", "(sen(x)/x)^(1/x^2)", "(x+1)^x", "x^(1/x)"],
)
def test_identificar_forma_termina_rapido(funcao):
    inicio = time.perf_counter()
    identificar_forma(ler_funcao(funcao), ler_ponto("0"))
    assert time.perf_counter() - inicio < 2


def test_passo_oo_sobre_zero_titulo_e_latex():
    passo = passo_forma_indeterminada(x, sp.Integer(0), "oo/0")
    assert passo.titulo == "Divisão de infinito por zero"
    assert r"\frac{\infty}{0}" in passo.latex


# ---------- técnica: fatoração em 0/0 ----------

@pytest.mark.parametrize(
    "funcao, ponto, esperado",
    [
        ("(x^2-4)/(x-2)", "2", 4),
        ("(x^2-1)/(x-1)", "1", 2),
        ("(x^3-8)/(x^2-4)", "2", 3),
        ("(x^2+x-6)/(x^2-4)", "2", sp.Rational(5, 4)),
        ("(x^2-5x+6)/(x-3)", "3", 1),
        ("(x-1)/(x^2-1)", "1", sp.Rational(1, 2)),
        ("(x^2-x)/(x^2+x)", "0", -1),
        ("(x^2-9)/(x+3)", "-3", -6),
        ("(x^2-1)/(x^2-2x+1)*(x-1)", "1", 2),
    ],
)
def test_fatoracao(funcao, ponto, esperado):
    expr, p = ler_funcao(funcao), ler_ponto(ponto)
    r = resolver(expr, p)
    assert r.resolvido and r.existe
    assert r.valor == esperado
    assert r.validado is True
    assert sp.limit(expr, x, p) == esperado
    titulos = [t.titulo for t in r.passos]
    assert "Fatoração" in titulos and "Cancelamento do fator comum" in titulos
    assert titulos[-1] == "Resultado"
    assert all(t.titulo and t.explicacao and t.latex for t in r.passos)


@pytest.mark.parametrize(
    "funcao, ponto",
    [
        ("x/x^2", "0"),                 # vira 1/x: k/0, sem limite
        ("(x-1)^2/(x-1)^3", "1"),       # vira 1/(x-1)
        ("sen(x)/x^2", "0"),            # não é racional
        ("(x^2-4)/(x-2)", "infinito"),  # ponto infinito
        ("(x+1)/(x-2)", "2"),           # k/0
    ],
)
def test_fatoracao_nao_resolve(funcao, ponto):
    r = _resolver(funcao, ponto)
    assert "Fatoração" not in [p.titulo for p in r.passos]
    if ponto == "infinito":
        # fatorar_e_cancelar não atua em ponto infinito; outra técnica desta
        # etapa (divisão pela maior potência) pode concluir no lugar dela.
        if r.resolvido:
            assert r.valor == sp.limit(ler_funcao(funcao), x, ler_ponto(ponto))
        else:
            assert r.valor is None
    else:
        _confere_com_sympy(r, funcao, ponto)  # quem conclui é a análise lateral


def test_fatoracao_respeita_limite_de_profundidade():
    expr, p = ler_funcao("(x^2-4)/(x-2)"), ler_ponto("2")
    from app.motor.resolvedor import PROFUNDIDADE_MAXIMA
    r = resolver(expr, p, PROFUNDIDADE_MAXIMA)
    assert "Fatoração" not in [t.titulo for t in r.passos]


def test_fatoracao_grau_alto_nao_trava():
    for grau in (1000, 500):
        inicio = time.perf_counter()
        r = _resolver(f"(x^{grau}-1)/(x-1)", "1")
        assert time.perf_counter() - inicio < 12
        assert "Fatoração" not in [p.titulo for p in r.passos]


def test_fatoracao_grau_100_resolve_rapido():
    inicio = time.perf_counter()
    r = _resolver("(x^100-1)/(x-1)", "1")
    assert time.perf_counter() - inicio < 2
    assert r.resolvido and r.valor == 100


def test_fatoracao_grau_dentro_do_limite_resolve():
    r = _resolver("(x^20-1)/(x-1)", "1")
    assert r.resolvido and r.valor == 20 and r.validado is True


@pytest.mark.parametrize(
    "funcao, ponto",
    [
        ("(x^2-4)/(x-2)^2", "2"),         # sobra k/0
        ("(x-1)/(x-1)^2", "1"),           # vira 1/(x-1)
        ("(x^2-2)/(x-sqrt(2))", "sqrt(2)"),
    ],
)
def test_fatoracao_sem_valor_errado(funcao, ponto):
    try:
        ponto_lido = ler_ponto(ponto)
    except ErroEntrada:
        pytest.skip("entrada não aceita esse ponto")
    r = resolver(ler_funcao(funcao), ponto_lido)
    _confere_com_sympy(r, funcao, ponto)


def test_fatoracao_com_constante_mostra_fator_monico():
    r = _resolver("(x^2-1/4)/(x-1/2)", "1/2")
    assert r.resolvido and r.valor == 1
    fat = next(p for p in r.passos if p.titulo == "Fatoração")
    assert "x - 1/2" in fat.explicacao
    assert r"\lim_{x \to \frac{1}{2}}" in fat.latex
    sub = next(p for p in r.passos if p.titulo == "Substituição direta")
    assert sub.latex.endswith("= 1")


def test_texto_e_latex_dos_passos_de_fatoracao():
    r = _resolver("(x^2-4)/(x-2)", "2")
    fat = next(p for p in r.passos if p.titulo == "Fatoração")
    canc = next(p for p in r.passos if p.titulo == "Cancelamento do fator comum")
    assert "aparece o fator x - 2 nos dois" in fat.explicacao
    assert fat.latex == (
        r"\lim_{x \to 2} \frac{x^{2} - 4}{x - 2} = \lim_{x \to 2} "
        r"\frac{\left(x - 2\right) \left(x + 2\right)}{x - 2}"
    )
    assert "nunca é" in canc.explicacao
    assert canc.latex.endswith(r"= \lim_{x \to 2} \left(x + 2\right)")
    assert r.passos[-2].latex == r"\lim_{x \to 2} \left(x + 2\right) = 2 + 2 = 4"


def test_validado_none_fora_da_fatoracao():
    assert _resolver("x+1", "2").validado is None
    assert _resolver("|x|/x", "0").validado is None  # laterais, sem conferência extra


def test_conferir_com_sympy_aceita_lado_e_ignora_expressao_grande():
    from app.motor.resolvedor import conferir_com_sympy
    assert conferir_com_sympy(1 / x, sp.Integer(0), sp.oo, "+") is True
    assert conferir_com_sympy(1 / x, sp.Integer(0), -sp.oo, "-") is True
    grande = sum(x**k for k in range(400))
    assert conferir_com_sympy(grande, sp.Integer(1), sp.Integer(400)) is None


# ---------- técnica: racionalização (conjugado) em 0/0 ----------

@pytest.mark.parametrize(
    "funcao, ponto, esperado",
    [
        ("(sqrt(x+1)-1)/x", "0", sp.Rational(1, 2)),
        ("x/(sqrt(x+4)-2)", "0", 4),
        ("(sqrt(x)-2)/(x-4)", "4", sp.Rational(1, 4)),
        ("(sqrt(x+3)-sqrt(3))/x", "0", sp.sqrt(3) / 6),
        ("(1-sqrt(1-x))/x", "0", sp.Rational(1, 2)),
        ("(sqrt(x)-1)/(x-1)", "1", sp.Rational(1, 2)),
        ("(sqrt(x+4)-2)/x", "0", sp.Rational(1, 4)),
        ("(sqrt(x+1)-sqrt(1-x))/x", "0", 1),
        ("x/(1-sqrt(1-x))", "0", 2),
        ("(sqrt(x+9)-3)/(sqrt(x+16)-4)", "0", sp.Rational(4, 3)),   # raiz nos dois lados
        ("(x^2-1)/(sqrt(x)-1)", "1", 4),
        ("(sqrt(x+5)-1)/(x+4)", "-4", sp.Rational(1, 2)),           # ponto negativo
        ("x/(sqrt(x)+x)", "0", 0),                                  # domínio só à direita
        ("(sqrt(x+0.5)-1)/(x-0.5)", "0.5", sp.Rational(1, 2)),   # decimal vira racional
    ],
)
def test_racionalizacao(funcao, ponto, esperado):
    expr, p = ler_funcao(funcao), ler_ponto(ponto)
    r = resolver(expr, p)
    assert r.resolvido and r.existe
    assert sp.simplify(r.valor - esperado) == 0
    assert r.validado is True
    assert sp.simplify(sp.limit(expr, x, p) - esperado) == 0
    titulos = [t.titulo for t in r.passos]
    for esperado_titulo in ("Conjugado", "Multiplicação pelo conjugado", "Simplificação"):
        assert esperado_titulo in titulos
    assert "Fatoração" not in titulos
    assert titulos[-1] == "Resultado"
    assert all(t.titulo and t.explicacao and t.latex for t in r.passos)


def test_racionalizacao_texto_e_latex():
    r = _resolver("(sqrt(x+1)-1)/x", "0")
    por_titulo = {p.titulo: p for p in r.passos}
    conj = por_titulo["Conjugado"]
    assert conj.latex == r"\sqrt{x + 1} - 1 \;\longrightarrow\; \sqrt{x + 1} + 1"
    assert "√(x + 1) + 1" in conj.explicacao and "numerador" in conj.explicacao
    mult = por_titulo["Multiplicação pelo conjugado"]
    assert (
        r"\left(\sqrt{x + 1} - 1\right)\left(\sqrt{x + 1} + 1\right) = "
        r"\left(\sqrt{x + 1}\right)^{2} - 1^{2} = \left(x + 1\right) - 1 = x"
    ) in mult.latex
    assert mult.latex.startswith(r"\begin{gathered}")
    assert r"\frac{\sqrt{x + 1} + 1}{\sqrt{x + 1} + 1}" in mult.latex
    assert "(a − b)(a + b) = a² − b²" in mult.explicacao
    simp = por_titulo["Simplificação"]
    assert simp.latex.endswith(r"= \lim_{x \to 0} \frac{1}{\sqrt{x + 1} + 1}")
    assert por_titulo["Resultado"].latex.endswith(r"= \frac{1}{2}")


def test_racionalizacao_denominador_diz_denominador():
    r = _resolver("x/(sqrt(x+4)-2)", "0")
    conj = next(p for p in r.passos if p.titulo == "Conjugado")
    assert "raiz no denominador" in conj.explicacao


@pytest.mark.parametrize(
    "funcao, ponto",
    [
        ("sqrt(x^2)/x", "0"),                    # laterais divergentes
        ("|x|/x", "0"),
        ("sen(x)/x^2", "0"),                     # sem raiz
        ("(sqrt(x+1)-1)/x", "infinito"),         # ponto infinito
        ("(sqrt(x+1)+1)/x", "0"),                # k/0, não 0/0
        ("(x^(1/3)-1)/(x-1)", "1"),              # raiz cúbica
    ],
)
def test_racionalizacao_nao_se_aplica(funcao, ponto):
    r = _resolver(funcao, ponto)
    assert "Conjugado" not in [p.titulo for p in r.passos]
    if ponto == "infinito":
        assert not r.resolvido and r.valor is None
    else:
        _confere_com_sympy(r, funcao, ponto)


def test_racionalizar_none_sem_erro():
    from app.motor.tecnicas import racionalizar
    for funcao in ["sqrt(x)/x", "x^2", "(x+1)/(x-1)"]:
        assert racionalizar(ler_funcao(funcao), sp.Integer(0)) is None


def test_racionalizacao_nao_regride_fatoracao():
    r = _resolver("(x^2-4)/(x-2)", "2")
    assert r.valor == 4
    assert "Conjugado" not in [p.titulo for p in r.passos]


def test_racionalizacao_nao_devolve_valor_errado():
    # (sqrt(x)+x)/x em 0 vai a +oo pela direita (só esse lado existe).
    r = _resolver("(sqrt(x)+x)/x", "0")
    assert r.resolvido and r.valor == sp.oo
    _confere_com_sympy(r, "(sqrt(x)+x)/x", "0")


# ---------- limite com timeout, conferência e passos honestos ----------

def test_limite_seguro_nao_trava_no_exemplo_ruim():
    inicio = time.perf_counter()
    expr = ler_funcao("(sqrt(x^2-2x+1)+x-1)/(x-1)")
    forma = identificar_forma(expr, sp.Integer(1))
    r = resolver(expr, sp.Integer(1))
    assert time.perf_counter() - inicio < 10
    assert forma in ("0/0", None)
    _confere_com_sympy(r, "(sqrt(x^2-2x+1)+x-1)/(x-1)", "1")


def test_limite_seguro_devolve_none_no_timeout(monkeypatch):
    from app.motor import seguro

    def lento(*args, **kwargs):
        time.sleep(30)

    monkeypatch.setattr(seguro.sp, "limit", lento)
    inicio = time.perf_counter()
    assert seguro.limite_seguro(1 / x, sp.Integer(0), "+", tempo=0.3) is None
    assert time.perf_counter() - inicio < 5


def test_limite_seguro_valores_normais():
    from app.motor.seguro import limite_seguro
    assert limite_seguro(sp.sin(x) / x, sp.Integer(0)) == 1
    assert limite_seguro(1 / x, sp.Integer(0), "+") == sp.oo
    assert limite_seguro(1 / x, sp.Integer(0), "-") == -sp.oo
    assert limite_seguro(sp.sqrt(x**2 - 2 * x + 1), sp.Integer(1)) == 0


def test_conferencia_divergente_descarta_passos_da_tecnica(monkeypatch):
    from app.motor import resolvedor
    monkeypatch.setattr(resolvedor, "conferir_com_sympy", lambda *a, **k: False)
    r = _resolver("(sqrt(x+1)-1)/x", "0")
    titulos = [p.titulo for p in r.passos]
    assert not r.resolvido and r.valor is None and r.validado is False
    assert titulos[-1] == "Conferência não coincidiu"
    assert "Conjugado" not in titulos and "Resultado" not in titulos
    assert "não coincidiram" in r.passos[-1].explicacao


def test_tecnica_que_nao_conclui_descarta_passos():
    r = _resolver("(x^2-4)/(x-2)^2", "2")   # a fatoração deixa k/0
    titulos = [p.titulo for p in r.passos]
    assert "Fatoração" not in titulos      # os passos da técnica foram descartados
    assert r.resolvido and not r.existe    # os laterais (−∞ e +∞) concluem
    assert titulos[-1].startswith("Os laterais são diferentes")


@pytest.mark.parametrize(
    "funcao, ponto",
    [
        ("(sqrt(x)-1)/(x-1)^2", "1"),    # tende a infinito
        ("sqrt(x)/x", "0"),              # k/0, só existe à direita
        ("(sqrt(x)+x)/x", "0"),
    ],
)
def test_racionalizacao_sem_valor_errado_em_casos_divergentes(funcao, ponto):
    r = _resolver(funcao, ponto)
    _confere_com_sympy(r, funcao, ponto)


def test_racionalizacao_raiz_nos_dois_lados_passos():
    r = _resolver("(sqrt(x+9)-3)/(sqrt(x+16)-4)", "0")
    assert r.resolvido and r.valor == sp.Rational(4, 3) and r.validado is True
    assert [p.titulo for p in r.passos].count("Conjugado") == 2
    primeiro = next(p for p in r.passos if p.titulo == "Conjugado")
    assert "também tem raiz" in primeiro.explicacao


def test_conjugado_respeita_ordem_e_sinais():
    r = _resolver("(1-sqrt(1-x))/x", "0")
    conj = next(p for p in r.passos if p.titulo == "Conjugado")
    assert conj.latex == r"1 - \sqrt{1 - x} \;\longrightarrow\; 1 + \sqrt{1 - x}"
    mult = next(p for p in r.passos if p.titulo == "Multiplicação pelo conjugado")
    assert r"1^{2} - \left(\sqrt{1 - x}\right)^{2} = 1 - \left(1 - x\right) = x" in mult.latex
    soma = _resolver("(sqrt(x+1)-sqrt(1-x))/x", "0")
    assert soma.valor == 1 and soma.validado is True


def test_simplificacao_diz_qual_fator_cancela():
    r = _resolver("(sqrt(x)-2)/(x-4)", "4")
    simp = next(p for p in r.passos if p.titulo == "Simplificação")
    assert "O fator x - 4 aparece" in simp.explicacao


def test_texto_do_resultado_usa_unicode():
    r = _resolver("(sqrt(x+3)-sqrt(3))/x", "0")
    assert "√" in r.passos[-1].explicacao and "sqrt" not in r.passos[-1].explicacao


# ---------- técnica: limites fundamentais em 0/0 ----------

@pytest.mark.parametrize(
    "funcao, ponto, esperado",
    [
        ("sen(x)/x", "0", 1),
        ("sen(3x)/x", "0", 3),
        ("sen(3x)/sen(5x)", "0", sp.Rational(3, 5)),
        ("tg(x)/x", "0", 1),
        ("tg(2x)/x", "0", 2),
        ("(1-cos(x))/x^2", "0", sp.Rational(1, 2)),
        ("(1-cos(2x))/x^2", "0", 2),
        ("(1-cos(x))/x", "0", 0),
        ("(e^x-1)/x", "0", 1),
        ("(e^(2x)-1)/x", "0", 2),
        ("ln(1+x)/x", "0", 1),
        ("ln(1+3x)/x", "0", 3),
        ("sen(x^2)/x^2", "0", 1),
        ("sen(x)/(2x)", "0", sp.Rational(1, 2)),
        ("x/sen(x)", "0", 1),
        ("sen(x)^2/x^2", "0", 1),
        ("(2^x-1)/x", "0", sp.log(2)),
        ("sen(x-1)/(x-1)", "1", 1),          # u = x - 1
        ("sen(2x-6)/(x-3)", "3", 2),
        ("x*sen(x)/x^2", "0", 1),
        ("sen(x)/(x^2+x)", "0", 1),          # o resto cai na fatoração
        ("(cos(x)-1)/x^2", "0", -sp.Rational(1, 2)),
        ("(2^(3x)-1)/x", "0", 3 * sp.log(2)),
        ("(e^(sen(x))-1)*(1+x)/(5x)", "0", sp.Rational(1, 5)),    # u = sen x
        ("(1-cos(sen(x)))*(x+2)/sen(x)", "0", 0),
    ],
)
def test_limites_fundamentais(funcao, ponto, esperado):
    expr, p = ler_funcao(funcao), ler_ponto(ponto)
    r = resolver(expr, p)
    assert r.resolvido and r.existe
    assert sp.simplify(r.valor - esperado) == 0
    assert r.validado is True
    assert sp.simplify(limite_seguro(expr, p) - esperado) == 0
    titulos = [t.titulo for t in r.passos]
    for titulo in ("Limite fundamental", "Ajuste algébrico"):
        assert titulo in titulos
    assert any(t.startswith("Limite do produto") for t in titulos)
    assert titulos[-1] == "Resultado"
    assert all(t.titulo and t.explicacao and t.latex for t in r.passos)


@pytest.mark.parametrize(
    "funcao, ponto",
    [
        ("sen(x)/x", "infinito"),       # u = x não tende a 0
        ("sen(x)/x^2", "0"),            # o resto 1/x diverge
        ("sen(1/x)/(1/x)", "0"),        # u = 1/x não tende a 0
        ("(x^2-4)/(x-2)", "2"),         # é fatoração, não fundamental
    ],
)
def test_limites_fundamentais_nao_se_aplicam(funcao, ponto):
    r = _resolver(funcao, ponto)
    titulos = [p.titulo for p in r.passos]
    assert "Limite fundamental" not in titulos
    if ponto == "infinito":
        # não é limite fundamental (u = x não tende a 0), mas é resolvido por
        # outra técnica: sen(x)/x no infinito é função limitada sobre infinito.
        assert r.resolvido and r.valor == 0
    else:
        _confere_com_sympy(r, funcao, ponto)


def test_fundamental_nao_e_usado_quando_fatoracao_resolve():
    r = _resolver("(x^2-1)/(x-1)", "1")
    assert r.valor == 2 and "Fatoração" in [p.titulo for p in r.passos]


def test_fundamental_texto_e_latex():
    r = _resolver("sen(3x)/x", "0")
    por_titulo = {p.titulo: p for p in r.passos}
    lf = por_titulo["Limite fundamental"]
    assert lf.latex == (
        r"\lim_{u \to 0} \frac{\sin u}{u} = 1, \quad u = 3 x, \quad "
        r"\lim_{x \to 0} \left(3 x\right) = 0"
    )
    assert "u = 3 · x" in lf.explicacao and "tende a 0" in lf.explicacao
    assert "sen(3 · x)" in lf.explicacao
    aj = por_titulo["Ajuste algébrico"]
    assert aj.latex.endswith(r"\lim_{x \to 0} \frac{\sin{\left(3 x \right)}}{3 x} \cdot 3")
    prod = por_titulo["Limite do produto"]
    assert "produto dos limites" in prod.explicacao
    assert prod.latex.endswith(r"= 1 \cdot \lim_{x \to 0} 3")
    assert r.passos[-1].latex.endswith("= 3")


def test_fundamental_no_denominador_mostra_inverso():
    r = _resolver("x/sen(x)", "0")
    aj = next(p for p in r.passos if p.titulo == "Ajuste algébrico")
    assert r"\frac{1}{\frac{\sin{\left(x \right)}}{x}}" in aj.latex


def test_fundamental_divergencia_descarta_passos(monkeypatch):
    from app.motor import resolvedor
    monkeypatch.setattr(resolvedor, "conferir_com_sympy", lambda *a, **k: False)
    r = _resolver("sen(3x)/x", "0")
    titulos = [p.titulo for p in r.passos]
    assert not r.resolvido and r.validado is False
    assert titulos[-1] == "Conferência não coincidiu"
    assert "Limite fundamental" not in titulos


# ---------- robustez: lados, timeout e conferência obrigatória ----------

@pytest.mark.parametrize(
    "funcao",
    [
        "sen(x*e^(-1/x))/(x*e^(-1/x))",   # u -> 0 só pela direita
        "sen(e^(-1/x))/e^(-1/x)",
        "sen(x)/|x|",                      # laterais diferentes
        "sen(pi*x)/(x-1)",                 # não é 0/0 em 0; testado em 1 abaixo
    ],
)
def test_fundamentais_nao_afirmam_valor_com_lados_diferentes(funcao):
    inicio = time.perf_counter()
    r = _resolver(funcao, "0" if "pi" not in funcao else "1")
    assert time.perf_counter() - inicio < 15
    assert "Limite fundamental" not in [p.titulo for p in r.passos]
    if funcao == "sen(x)/|x|":
        assert r.resolvido and not r.existe and (r.esquerda, r.direita) == (-1, 1)
    elif "pi" in funcao:
        assert r.resolvido and r.valor == -sp.pi
    else:
        _confere_com_sympy(r, funcao, "0")


def test_definida_no_lado_tem_timeout(monkeypatch):
    from app.motor import formas

    def lenta(*args, **kwargs):
        time.sleep(30)

    monkeypatch.setattr(formas, "_amostra_real", lenta)
    monkeypatch.setattr(formas, "executar_com_timeout",
                        lambda f, *a, **k: formas_original(f, *a, tempo=0.3))
    inicio = time.perf_counter()
    assert formas.definida_no_lado(x, sp.Integer(0), "+") is None
    assert time.perf_counter() - inicio < 5


def formas_original(f, *a, tempo):
    from app.motor.seguro import executar_com_timeout
    return executar_com_timeout(f, *a, tempo=tempo)


def test_forma_none_quando_lado_nao_confiavel(monkeypatch):
    from app.motor import formas
    monkeypatch.setattr(formas, "definida_no_lado", lambda *a, **k: None)
    assert identificar_forma(ler_funcao("sen(x)/x"), sp.Integer(0)) is None


def test_sem_conferencia_nao_afirma_valor(monkeypatch):
    from app.motor import resolvedor
    monkeypatch.setattr(resolvedor, "conferir_com_sympy", lambda *a, **k: None)
    monkeypatch.setattr(resolvedor, "calcular_laterais", lambda *a, **k: None)
    r = _resolver("(x^2-4)/(x-2)", "2")
    assert not r.resolvido and r.valor is None
    assert r.passos[-1].titulo == "Não conseguimos concluir"
    assert "confirmar" in r.passos[-1].explicacao
    # substituição direta pura continua resolvendo sem conferência
    assert _resolver("x+1", "2").resolvido


def test_substituicao_direta_constante_sem_igualdade_repetida():
    r = _resolver("sen(3x)/sen(5x)", "0")
    ultimo_sub = [p for p in r.passos if p.titulo == "Substituição direta"][-1]
    assert ultimo_sub.latex == r"\lim_{x \to 0} \frac{3}{5} = \frac{3}{5}"


def test_texto_quociente_e_ln():
    r = _resolver("sen(3x)/sen(5x)", "0")
    prod = next(p for p in r.passos if p.titulo.startswith("Limite do produto"))
    assert prod.titulo == "Limite do produto e do quociente"
    assert "quociente" in prod.explicacao and "diferente de 0" in prod.explicacao
    r2 = _resolver("(2^x-1)/x", "0")
    assert "ln(2)" in r2.passos[-1].explicacao and "log" not in r2.passos[-1].explicacao
    r3 = _resolver("sen(x)^2/x^2", "0")
    assert "sen²(x)" in next(p for p in r3.passos if p.titulo == "Limite fundamental").explicacao
    lf = next(p for p in r3.passos if p.titulo == "Limite fundamental")
    assert r"\left(x\right)" not in lf.latex


# ======================= Etapa 3: laterais, k/0 e domínio =======================

from app.motor.laterais import (  # noqa: E402
    Laterais, analisar_sinais, calcular_laterais, concluir,
)

oo = sp.oo


@pytest.mark.parametrize(
    "funcao, ponto, existe, valor, esquerda, direita",
    [
        # k/0 com análise de sinal
        ("1/x", "0", False, None, -oo, oo),
        ("1/x^2", "0", True, oo, oo, oo),
        ("-1/x^2", "0", True, -oo, -oo, -oo),
        ("1/(x-1)", "1", False, None, -oo, oo),
        ("1/(x-1)^2", "1", True, oo, oo, oo),
        ("(x+1)/(x-2)", "2", False, None, -oo, oo),
        ("(x-3)/(x-2)^2", "2", True, -oo, -oo, -oo),
        ("1/(1-x)", "1", False, None, oo, -oo),
        ("(x^2-1)/(x^2+2x+1)", "-1", False, None, oo, -oo),
        ("tg(x)", "pi/2", False, None, oo, -oo),
        # 0/0 que sobra como k/0 depois de simplificar
        ("(x^2-4)/(x-2)^2", "2", False, None, -oo, oo),
        ("sen(x)/x^2", "0", False, None, -oo, oo),
        ("(1-cos(x))/x^3", "0", False, None, -oo, oo),
        # laterais finitos e diferentes
        ("|x|/x", "0", False, None, -1, 1),
        ("sqrt(x^2)/x", "0", False, None, -1, 1),
        ("sen(x)/|x|", "0", False, None, -1, 1),
        ("piso(x)", "0", False, None, -1, 0),
        ("piso(x)", "2", False, None, 1, 2),
        # laterais iguais
        ("|x|", "0", True, 0, 0, 0),
        ("x*|x|/x", "0", True, 0, 0, 0),
        # função definida de um lado só
        ("ln(x)", "0", True, -oo, None, -oo),
        ("sqrt(x)/x", "0", True, oo, None, oo),
        ("x^x", "0", True, 1, None, 1),
        ("x*ln(x)", "0", True, 0, None, 0),
        ("sqrt(x)", "0", True, 0, None, 0),
        ("sqrt(-x)", "0", True, 0, 0, None),
        ("ln(1-x)", "1", True, -oo, -oo, None),
    ],
)
def test_laterais_e_k_sobre_zero(funcao, ponto, existe, valor, esquerda, direita):
    r = _resolver(funcao, ponto)
    assert r.resolvido
    assert r.existe is existe
    assert r.valor == valor
    assert (r.esquerda, r.direita) == (esquerda, direita)
    _confere_com_sympy(r, funcao, ponto)
    assert all(p.titulo and p.explicacao and p.latex for p in r.passos)


def test_zoo_nunca_e_devolvido_como_valor():
    for funcao, ponto in [("1/x", "0"), ("1/(x-1)", "1"), ("tg(x)", "pi/2")]:
        r = _resolver(funcao, ponto)
        assert r.valor is None and not r.existe


def test_x_elevado_a_x_em_zero_so_considera_o_lado_direito():
    r = _resolver("x^x", "0")
    titulos = [p.titulo for p in r.passos]
    assert "Função definida de um lado só" in titulos
    lado = next(p for p in r.passos if p.titulo == "Limites laterais")
    assert "direita" in lado.explicacao and "não está definida" in lado.explicacao


def test_passos_k_sobre_zero_mostram_o_sinal_de_cada_lado():
    r = _resolver("1/x", "0")
    titulos = [p.titulo for p in r.passos]
    assert titulos[:3] == [
        "Limite a calcular", "Tentativa de substituição direta", "Divisão por zero"]
    assert titulos[-3:] == [
        "Limites laterais", "Análise de sinal (divisão por zero)",
        "Os laterais são diferentes: o limite não existe"]
    sinal = next(p for p in r.passos if p.titulo.startswith("Análise de sinal"))
    assert "esquerda" in sinal.explicacao and "direita" in sinal.explicacao
    assert "negativo" in sinal.explicacao and "−∞" in sinal.explicacao
    assert "+∞" in sinal.explicacao
    assert r"\lim_{x \to 0^{-}} \frac{1}{x} = -\infty" in sinal.latex
    assert r"\lim_{x \to 0^{+}} \frac{1}{x} = \infty" in sinal.latex
    assert r.validado is True  # o sinal amostrado concorda com o SymPy


def test_k_sobre_zero_com_mesmo_sinal_dos_dois_lados_tem_limite_infinito():
    r = _resolver("1/x^2", "0")
    conclusao = r.passos[-1]
    assert conclusao.titulo == "Os laterais coincidem"
    assert "existe e vale ∞" in conclusao.explicacao
    assert conclusao.latex.endswith(r"= \infty")


def test_laterais_diferentes_texto_e_latex():
    r = _resolver("|x|/x", "0")
    ultimo = r.passos[-1]
    assert ultimo.titulo == "Os laterais são diferentes: o limite não existe"
    assert "Pela esquerda o limite é -1 e pela direita é 1" in ultimo.explicacao
    assert r"-1 \neq 1" in ultimo.latex and "não existe" in ultimo.latex
    assert r.validado is None  # sem análise de sinal (não é k/0)


def test_passo_laterais_texto_e_latex():
    r = _resolver("piso(x)", "0")
    p = next(p for p in r.passos if p.titulo == "Limites laterais")
    assert "esquerda, x → 0⁻" in p.explicacao and "direita, x → 0⁺" in p.explicacao
    assert r"\lim_{x \to 0^{-}}" in p.latex and r"\lim_{x \to 0^{+}}" in p.latex
    assert "-1" in p.latex and "0" in p.latex


def test_substituicao_direta_ja_preenche_laterais():
    r = _resolver("x^2+1", "3")
    assert (r.esquerda, r.direita) == (10, 10) and r.valor == 10


def test_tecnica_resolvida_tambem_informa_laterais():
    r = _resolver("(x^2-4)/(x-2)", "2")
    assert r.valor == 4 and (r.esquerda, r.direita) == (4, 4)
    r = _resolver("(sqrt(x)+x)/x", "0")
    assert r.valor == oo and (r.esquerda, r.direita) == (None, oo)


def test_ponto_infinito_nao_usa_laterais():
    r = _resolver("x/sen(x)", "infinito")
    assert not r.resolvido
    assert calcular_laterais(ler_funcao("x/sen(x)"), oo) is None
    assert all(p.titulo != "Limites laterais" for p in r.passos)


def test_fora_do_dominio_dos_dois_lados_nao_tem_limite():
    assert calcular_laterais(ler_funcao("sqrt(x)"), sp.Integer(-1)) is None
    r = _resolver("sqrt(x)", "-1")
    assert not r.resolvido


def test_calcular_laterais_unidade():
    lat = calcular_laterais(ler_funcao("1/x"), sp.Integer(0))
    assert (lat.esquerda, lat.direita) == (-oo, oo)
    assert lat.lados() == ["-", "+"]
    lat = calcular_laterais(ler_funcao("ln(x)"), sp.Integer(0))
    assert lat.esquerda is None and lat.direita == -oo and lat.lados() == ["+"]


@pytest.mark.parametrize(
    "esquerda, direita, existe, valor",
    [
        (1, 1, True, 1),
        (oo, oo, True, oo),
        (-oo, -oo, True, -oo),
        (sp.Rational(1, 2), sp.Rational(2, 4), True, sp.Rational(1, 2)),
        (1, 2, False, None),
        (-oo, oo, False, None),
        (oo, -oo, False, None),
        (None, 3, True, 3),
        (3, None, True, 3),
        (None, oo, True, oo),
    ],
)
def test_concluir(esquerda, direita, existe, valor):
    c = concluir(Laterais(esquerda, direita))
    assert c.existe is existe and c.valor == valor


def test_analise_de_sinal_unidade():
    expr, ponto = ler_funcao("(x-3)/(x-2)^2"), sp.Integer(2)
    lat = calcular_laterais(expr, ponto)
    analises = analisar_sinais(expr, ponto, lat)
    assert [(a.lado, a.sinal_numerador, a.sinal_denominador, a.resultado)
            for a in analises] == [("-", -1, 1, -oo), ("+", -1, 1, -oo)]


def test_analise_de_sinal_nao_se_aplica_a_laterais_finitos():
    expr, ponto = ler_funcao("|x|/x"), sp.Integer(0)
    assert analisar_sinais(expr, ponto, calcular_laterais(expr, ponto)) is None


def test_analise_de_sinal_discordante_nao_explica():
    # sinais amostrados não batem com o limite informado: não inventamos explicação
    expr, ponto = ler_funcao("1/x"), sp.Integer(0)
    errado = Laterais(esquerda=oo, direita=oo)
    assert analisar_sinais(expr, ponto, errado) is None


def test_divergencia_da_tecnica_nao_e_escondida_pelos_laterais(monkeypatch):
    from app.motor import resolvedor
    monkeypatch.setattr(resolvedor, "conferir_com_sympy", lambda *a, **k: False)
    r = _resolver("(x^2-4)/(x-2)", "2")
    assert not r.resolvido and r.validado is False
    assert r.passos[-1].titulo == "Conferência não coincidiu"


def test_laterais_sem_resposta_do_sympy_nao_afirmam_nada(monkeypatch):
    from app.motor import laterais as modulo
    monkeypatch.setattr(modulo, "limite_seguro", lambda *a, **k: None)
    assert calcular_laterais(ler_funcao("1/x"), sp.Integer(0)) is None
    r = _resolver("1/x", "0")
    assert not r.resolvido and r.valor is None


@pytest.mark.parametrize(
    "funcao",
    ["sen(1/x)", "x*sen(1/x)", "sen(x*e^(-1/x))/(x*e^(-1/x))", "cos(1/x)"],
)
def test_laterais_oscilantes_ou_lentos_terminam_sem_valor_errado(funcao):
    inicio = time.perf_counter()
    r = _resolver(funcao, "0")
    assert time.perf_counter() - inicio < 15
    _confere_com_sympy(r, funcao, "0")


@pytest.mark.parametrize(
    "funcao, ponto",
    [
        ("1/x", "0"), ("1/x^3", "0"), ("1/(x+2)", "-2"), ("1/(x-1/2)", "1/2"),
        ("(x+5)/(x^2-9)", "3"), ("(x+5)/(x^2-9)", "-3"), ("x/(x-pi)", "pi"),
        ("1/(x^2-2x+1)", "1"), ("(2-x)/(x-1)^3", "1"), ("e^x/x", "0"),
        ("ln(x)/x", "0"), ("ln(x)/x^2", "0"), ("1/ln(x)", "1"), ("1/sen(x)", "0"),
        ("tg(x)", "pi/2"), ("1/tg(x)", "0"), ("sqrt(x)/(x-1)", "1"),
        ("1/sqrt(x)", "0"), ("x/|x|", "0"), ("|x-1|/(x-1)", "1"),
        ("piso(x)/x", "0"), ("piso(x)", "-3"), ("sen(x)/|x|", "0"),
        ("(x^2-1)/(x-1)^2", "1"), ("(x+1)/(x^2-1)", "1"), ("(x-2)/(x^2-4x+4)", "2"),
        ("ln(x)", "0"), ("sqrt(x)*ln(x)", "0"), ("x^x", "0"), ("x^(2x)", "0"),
    ],
)
def test_etapa_3_confere_com_sympy(funcao, ponto):
    inicio = time.perf_counter()
    r = _resolver(funcao, ponto)
    assert time.perf_counter() - inicio < 15
    _confere_com_sympy(r, funcao, ponto)
    if r.resolvido:
        assert r.valor != sp.zoo and not (r.valor is not None and r.valor.has(sp.nan, sp.zoo))
        assert all(p.titulo and p.explicacao and p.latex for p in r.passos)


def test_nenhum_passo_antigo_regride_com_os_laterais():
    for funcao, ponto, esperado in [
        ("(x^2-4)/(x-2)", "2", 4), ("(sqrt(x+1)-1)/x", "0", sp.Rational(1, 2)),
        ("sen(3x)/x", "0", 3), ("x+1", "2", 3),
    ]:
        r = _resolver(funcao, ponto)
        assert r.valor == esperado
        assert "Limites laterais" not in [p.titulo for p in r.passos]


@pytest.mark.parametrize(
    "funcao, ponto",
    [
        ("x^x", "-1"),               # (-1)^(-1) = -1, mas x^x não é real perto de -1
        ("x^(1/x)", "-1"),
        ("ln(x+1)/sqrt(x)", "-2"),   # (iπ)/(i√2) é real por coincidência
        ("sqrt(x)", "-1"),
        ("ln(x)", "-1"),
    ],
)
def test_ponto_isolado_fora_do_dominio_nao_tem_limite(funcao, ponto):
    r = _resolver(funcao, ponto)
    assert not r.resolvido and r.valor is None
    assert (r.esquerda, r.direita) == (None, None)
    tentativa = next(p for p in r.passos if p.titulo == "Tentativa de substituição direta")
    assert "domínio" in tentativa.explicacao or "não está definida" in tentativa.explicacao


@pytest.mark.parametrize(
    "funcao, ponto, esperado",
    [("sqrt(x)", "4", 2), ("ln(x)", "e", 1), ("x^x", "2", 4), ("sqrt(x)", "0", 0),
     ("x^(1/3)", "8", 2), ("(x^2+1)/(x-3)", "1", -1), ("sen(x)+e^x", "0", 1)],
)
def test_substituicao_direta_continua_valendo_dentro_do_dominio(funcao, ponto, esperado):
    r = _resolver(funcao, ponto)
    assert r.resolvido and r.valor == esperado
    assert [p.titulo for p in r.passos][-1] == "Substituição direta"


# ======================= Etapa 4: limites no infinito =======================

from app.motor.tecnicas import termo_dominante  # noqa: E402


@pytest.mark.parametrize(
    "funcao, ponto, esperado",
    [
        ("3x^3-5x+1", "infinito", oo),      # grau ímpar, coef. positivo
        ("3x^3-5x+1", "-infinito", -oo),    # grau ímpar: inverte em -oo
        ("-2x^4+x", "infinito", -oo),       # grau par, coef. negativo
        ("-2x^4+x", "-infinito", -oo),      # grau par: mesmo sinal nos dois lados
        ("x^2-x^3", "infinito", -oo),       # termo dominante é -x^3
        ("x^2-x^3", "-infinito", oo),
        ("x^2", "infinito", oo),
        ("x^2", "-infinito", oo),
        ("-x^2", "infinito", -oo),
        ("-x^2", "-infinito", -oo),
        ("x", "infinito", oo),              # caso mais simples (sanity check)
        ("x", "-infinito", -oo),
        ("-x", "infinito", -oo),
        ("-x", "-infinito", oo),
        ("5", "infinito", 5),               # constante: caso trivial
        ("5", "-infinito", 5),
        ("x^2+3x-7", "infinito", oo),
        ("x^5-100x^4", "infinito", oo),
        ("x^5-100x^4", "-infinito", -oo),
        ("x^50-3x^49+1", "infinito", oo),     # grau alto, par
        ("x^50-3x^49+1", "-infinito", oo),
        ("(1/3)*x^3", "infinito", oo),        # coeficiente fracionário
        ("(1/3)*x^3", "-infinito", -oo),
        ("sqrt(2)*x^2", "infinito", oo),      # coeficiente irracional
        ("sqrt(2)*x^2", "-infinito", oo),
        ("-sqrt(3)*x^5", "infinito", -oo),    # coeficiente irracional negativo
        ("-sqrt(3)*x^5", "-infinito", oo),
        ("x^3-x^3+x^2", "infinito", oo),      # cancelamento: grau real é 2, não 3
        ("x^3-x^3+x^2", "-infinito", oo),
    ],
)
def test_termo_dominante_resolve(funcao, ponto, esperado):
    r = _resolver(funcao, ponto)
    assert r.resolvido and r.existe and r.valor == esperado
    assert sp.limit(ler_funcao(funcao), x, ler_ponto(ponto)) == esperado
    titulos = [p.titulo for p in r.passos]
    assert titulos[-1] == "Resultado"
    assert any(t in ("Termo de maior grau domina", "Função constante") for t in titulos)
    assert all(p.titulo and p.explicacao and p.latex for p in r.passos)


def test_termo_dominante_passo_constante():
    r = _resolver("5", "infinito")
    titulos = [p.titulo for p in r.passos]
    assert titulos == ["Limite a calcular", "Função constante", "Resultado"]


def test_termo_dominante_passo_grau_maior_que_zero():
    r = _resolver("3x^3-5x+1", "infinito")
    titulos = [p.titulo for p in r.passos]
    assert titulos == ["Limite a calcular", "Termo de maior grau domina", "Resultado"]
    passo = r.passos[1]
    assert "3" in passo.explicacao and "x^{3}" in passo.latex
    assert "+\\infty" in passo.latex or r"\infty" in passo.latex


@pytest.mark.parametrize("funcao", ["x^7", "(1/3)*x^3", "sqrt(2)*x^2", "|x|^4"])
def test_termo_dominante_passo_sem_repeticao_quando_e_um_termo_so(funcao):
    # Quando o polinômio já é só o termo de maior grau, não deve repetir a
    # mesma expressão nos dois lados de "=" nem falar de "termos de grau
    # menor" (não há nenhum).
    r = _resolver(funcao, "infinito")
    passo = r.passos[1]
    assert passo.titulo == "Termo de maior grau domina"
    assert passo.latex.count("=") == 1
    assert "grau menor" not in passo.explicacao


@pytest.mark.parametrize(
    "funcao, ponto",
    [
        ("x^2+1", "2"),                  # ponto finito: a técnica é só para o infinito
        ("(x^2-4)/(x-2)", "infinito"),   # função racional, não polinômio puro
        ("1/x", "-infinito"),            # função racional
        ("sen(x)", "infinito"),          # não é polinômio
        ("x^(1/2)", "infinito"),         # raiz: não é polinômio
    ],
)
def test_termo_dominante_nao_se_aplica(funcao, ponto):
    assert termo_dominante(ler_funcao(funcao), ler_ponto(ponto)) is None


def test_termo_dominante_nao_se_aplica_mas_racional_e_resolvida_por_outra_tecnica():
    # (x^2-4)/(x-2) não é polinômio puro, então termo_dominante não se aplica;
    # mas é uma função racional, resolvida por divisao_maior_potencia (abaixo).
    assert termo_dominante(ler_funcao("(x^2-4)/(x-2)"), ler_ponto("infinito")) is None
    r = _resolver("(x^2-4)/(x-2)", "infinito")
    assert r.resolvido and r.existe and r.valor == oo


def test_termo_dominante_nao_se_aplica_mas_e_resolvida_por_limitada_sobre_infinito():
    # k/polinômio (1/x) não é ∞/∞ (o numerador não cresce): não é
    # termo_dominante nem divisao_maior_potencia, mas é resolvida pela
    # técnica de função limitada sobre infinito (1 é limitada, x -> oo).
    assert termo_dominante(ler_funcao("1/x"), ler_ponto("infinito")) is None
    assert divisao_maior_potencia(ler_funcao("1/x"), ler_ponto("infinito")) is None
    r = _resolver("1/x", "infinito")
    assert r.resolvido and r.existe and r.valor == 0


def test_termo_dominante_divergencia_nao_e_escondida(monkeypatch):
    from app.motor import resolvedor
    monkeypatch.setattr(resolvedor, "conferir_com_sympy", lambda *a, **k: False)
    r = _resolver("x^3", "infinito")
    assert not r.resolvido and r.validado is False
    assert r.passos[-1].titulo == "Conferência não coincidiu"


def test_termo_dominante_polinomio_grande_nao_e_confirmado():
    # Polinômio grande o suficiente para passar de TAMANHO_MAXIMO_CONFERENCIA
    # (sp.count_ops): conferir_com_sympy devolve None, e a técnica não afirma
    # o valor, mesmo que ele esteja matematicamente correto.
    from app.motor.resolvedor import TAMANHO_MAXIMO_CONFERENCIA, resolver

    expr = sp.expand(sum(x**i for i in range(1, 160)))
    assert sp.count_ops(expr) > TAMANHO_MAXIMO_CONFERENCIA

    r = resolver(expr, sp.oo)
    assert not r.resolvido and r.valor is None and r.validado is None
    titulos = [p.titulo for p in r.passos]
    assert "Termo de maior grau domina" in titulos
    assert titulos[-1] == "Não conseguimos concluir"


# ================ Etapa 4: divisão pela maior potência (∞/∞) ================

from app.motor.tecnicas import divisao_maior_potencia  # noqa: E402


@pytest.mark.parametrize(
    "funcao, ponto, esperado",
    [
        # grau do numerador menor que o do denominador: limite 0
        ("(x+1)/(x^2+1)", "infinito", 0),
        ("(x+1)/(x^2+1)", "-infinito", 0),
        ("x/(x^2+1)", "infinito", 0),          # numerador cresce, mas mais devagar
        ("(x^3-1)/(x^5+1)", "-infinito", 0),
        # graus iguais: razão dos coeficientes líderes
        ("(2x+1)/(3x-5)", "infinito", sp.Rational(2, 3)),
        ("(2x+1)/(3x-5)", "-infinito", sp.Rational(2, 3)),
        ("(3x^2+2x)/(5x^2-1)", "infinito", sp.Rational(3, 5)),
        ("(-x+4)/(2x+1)", "infinito", sp.Rational(-1, 2)),
        ("(x^2-9)/(x^2+9)", "-infinito", 1),
        # grau do numerador maior: ±∞, com sinal a conferir
        ("(x^2-4)/(x-2)", "infinito", oo),
        ("(x^2-1)/(x+1)", "-infinito", -oo),
        ("(5-x^2)/(2x+3)", "infinito", -oo),
        ("(1-x^3)/(x^2+4)", "-infinito", oo),
        ("(x^4-1)/(x^2+1)", "-infinito", oo),
        ("x^3/(x+1)", "infinito", oo),
        ("x^3/(x+1)", "-infinito", oo),       # grau restante 2 (par): mesmo sinal nos dois lados
    ],
)
def test_divisao_maior_potencia_resolve(funcao, ponto, esperado):
    r = _resolver(funcao, ponto)
    assert r.resolvido and r.existe and r.valor == esperado
    assert sp.limit(ler_funcao(funcao), x, ler_ponto(ponto)) == esperado
    titulos = [p.titulo for p in r.passos]
    assert titulos[-1] == "Resultado"
    assert "Divisão pela maior potência" in titulos
    assert "Limite termo a termo" in titulos
    assert all(p.titulo and p.explicacao and p.latex for p in r.passos)


@pytest.mark.parametrize(
    "funcao, ponto",
    [
        ("(x+1)/(x^2+1)", "2"),       # ponto finito: a técnica é só para o infinito
        ("x^2+1", "infinito"),        # polinômio puro: já resolvido por termo_dominante
        ("1/x", "infinito"),          # k/polinômio: numerador não depende de x
        ("1/(x^2-3)", "infinito"),    # idem: numerador constante, não ∞/∞
        ("(x+1)/5", "infinito"),      # polinômio/k: denominador não depende de x
        ("sen(x)/x", "infinito"),     # numerador não é polinômio
        ("x/sen(x)", "infinito"),     # denominador não é polinômio
    ],
)
def test_divisao_maior_potencia_nao_se_aplica(funcao, ponto):
    assert divisao_maior_potencia(ler_funcao(funcao), ler_ponto(ponto)) is None


def test_divisao_maior_potencia_passos_mostram_cada_caso():
    r = _resolver("(x+1)/(x^2+1)", "infinito")
    passo = next(p for p in r.passos if p.titulo == "Limite termo a termo")
    assert "tende a 0" in passo.explicacao

    r = _resolver("(2x+1)/(3x-5)", "infinito")
    passo = next(p for p in r.passos if p.titulo == "Limite termo a termo")
    assert "razão" in passo.explicacao

    r = _resolver("(x^2-4)/(x-2)", "infinito")
    passo = next(p for p in r.passos if p.titulo == "Limite termo a termo")
    assert "cresce sem limite" in passo.explicacao


def test_divisao_maior_potencia_divergencia_nao_e_escondida(monkeypatch):
    from app.motor import resolvedor
    monkeypatch.setattr(resolvedor, "conferir_com_sympy", lambda *a, **k: False)
    r = _resolver("(2x+1)/(3x-5)", "infinito")
    assert not r.resolvido and r.validado is False
    assert r.passos[-1].titulo == "Conferência não coincidiu"


# ============== Etapa 4: função limitada sobre infinito (confronto) =========

from app.motor.tecnicas import limitada_sobre_infinito  # noqa: E402


@pytest.mark.parametrize(
    "funcao, ponto",
    [
        ("sen(x)/x", "infinito"),
        ("sen(x)/x", "-infinito"),
        ("cos(x)/x", "infinito"),
        ("cos(x)/x", "-infinito"),
        ("1/x", "infinito"),
        ("1/x", "-infinito"),
        ("1/x^2", "infinito"),
        ("1/x^2", "-infinito"),
        ("(2+sen(x))/x", "infinito"),      # numerador limitado entre 1 e 3
        ("(2+sen(x))/x", "-infinito"),
        ("1/(x^2-3)", "infinito"),         # numerador constante: caso particular
        ("sen(x)/x^2", "-infinito"),
        ("cos(x)/x^3", "-infinito"),
        ("-sen(x)/x", "infinito"),         # constante negativa multiplicando
        ("3*cos(x)/x^2", "infinito"),      # numerador limitado entre -3 e 3
    ],
)
def test_limitada_sobre_infinito_resolve(funcao, ponto):
    r = _resolver(funcao, ponto)
    assert r.resolvido and r.existe and r.valor == 0
    assert sp.limit(ler_funcao(funcao), x, ler_ponto(ponto)) == 0
    titulos = [p.titulo for p in r.passos]
    assert titulos[-1] == "Resultado"
    assert "Numerador limitado, denominador infinito" in titulos
    assert "Teorema do confronto" in titulos
    assert all(p.titulo and p.explicacao and p.latex for p in r.passos)


@pytest.mark.parametrize(
    "funcao, ponto",
    [
        ("sen(x)/sen(x)", "infinito"),    # simplifica para a constante 1, sem divisão relevante
        ("x/sen(x)", "infinito"),         # quem oscila é o denominador, não o numerador
        ("sen(x)", "infinito"),           # sem denominador: só oscila, sem limite
        ("x*sen(x)", "infinito"),         # produto, não quociente: cresce oscilando
        ("x*cos(x)", "-infinito"),
        ("(x+1)/(x^2+1)", "infinito"),    # numerador não limitado (cresce com x)
        ("x^2+1", "infinito"),            # polinômio puro, sem denominador que importe
        ("sen(x)/x", "2"),                # ponto finito: a técnica é só para o infinito
        ("sen(x)*cos(x)/x", "infinito"),  # produto de duas partes com x: não cobrimos
    ],
)
def test_limitada_sobre_infinito_nao_se_aplica(funcao, ponto):
    assert limitada_sobre_infinito(ler_funcao(funcao), ler_ponto(ponto)) is None


def test_limitada_sobre_infinito_nao_e_usada_quando_outra_tecnica_resolve():
    # x/sen(x) e sen(x) continuam sem solução (não é escopo desta etapa).
    for funcao in ("x/sen(x)", "sen(x)", "x*sen(x)"):
        r = _resolver(funcao, "infinito")
        assert not r.resolvido and r.valor is None


def test_limitada_sobre_infinito_bounds_mais_apertados_que_menos_um_e_um():
    # (2+sen(x))/x: o numerador fica entre 1 e 3, não só entre -1 e 1.
    r = _resolver("(2+sen(x))/x", "infinito")
    passo = next(p for p in r.passos if p.titulo == "Numerador limitado, denominador infinito")
    assert "1" in passo.explicacao and "3" in passo.explicacao
    assert "1" in passo.latex and "3" in passo.latex


def test_limitada_sobre_infinito_passo_numerador_constante():
    r = _resolver("1/(x^2-3)", "infinito")
    passo = next(p for p in r.passos if p.titulo == "Numerador limitado, denominador infinito")
    assert "constante" in passo.explicacao


def test_limitada_sobre_infinito_passo_oscilante():
    r = _resolver("sen(x)/x", "infinito")
    passo = next(p for p in r.passos if p.titulo == "Numerador limitado, denominador infinito")
    assert "oscilando" in passo.explicacao


def test_limitada_sobre_infinito_confronto_mostra_modulo():
    r = _resolver("sen(x)/x", "infinito")
    passo = next(p for p in r.passos if p.titulo == "Teorema do confronto")
    assert r"\left|" in passo.latex and r"\to 0" in passo.latex


def test_limitada_sobre_infinito_divergencia_nao_e_escondida(monkeypatch):
    from app.motor import resolvedor
    monkeypatch.setattr(resolvedor, "conferir_com_sympy", lambda *a, **k: False)
    r = _resolver("sen(x)/x", "infinito")
    assert not r.resolvido and r.validado is False
    assert r.passos[-1].titulo == "Conferência não coincidiu"


def test_limitada_sobre_infinito_nao_atrapalha_divisao_maior_potencia():
    # (x+1)/(x^2+1) continua sendo resolvido por divisao_maior_potencia, e não
    # por esta técnica (o numerador cresce, não é limitado).
    r = _resolver("(x+1)/(x^2+1)", "infinito")
    titulos = [p.titulo for p in r.passos]
    assert r.resolvido and r.valor == 0
    assert "Divisão pela maior potência" in titulos
    assert "Numerador limitado, denominador infinito" not in titulos
