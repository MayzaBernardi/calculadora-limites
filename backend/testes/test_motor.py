import time

import pytest
import sympy as sp

from app.motor.entrada import ErroEntrada, ler_funcao, ler_ponto, x
from app.motor.formas import identificar_forma, limite_da_parte
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
        ("(x^2-4)/(x-2)", "infinito"),  # ainda não tratado (etapa 4)
        ("sen(x)/x", "0"),        # 0/0
        ("1/x", "0"),             # k/0
        ("x^x", "0"),             # 0^0 não vale 1 em limites
        ("sqrt(x)", "-1"),        # fora do domínio
        ("ln(x)", "-1"),          # fora do domínio
        ("piso(x)", "2"),         # descontínua
        ("1/x", "infinito"),      # ainda não tratado (etapa 4)
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


def test_zero_sobre_zero_registra_passo_sem_resolver():
    r = _resolver("sen(x)/x", "0")  # ainda sem técnica (limites fundamentais)
    assert not r.resolvido
    assert [p.titulo for p in r.passos][-1] == "Indeterminação 0/0"
    assert "simplificar" in r.passos[-1].explicacao
    assert r.passos[-1].latex


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
        ("sen(x)/x", "0"),              # não é racional
        ("(x^2-4)/(x-2)", "infinito"),  # ponto infinito
        ("(x+1)/(x-2)", "2"),           # k/0
    ],
)
def test_fatoracao_nao_resolve(funcao, ponto):
    r = _resolver(funcao, ponto)
    assert not r.resolvido and r.valor is None


def test_fatoracao_respeita_limite_de_profundidade():
    expr, p = ler_funcao("(x^2-4)/(x-2)"), ler_ponto("2")
    from app.motor.resolvedor import PROFUNDIDADE_MAXIMA
    assert not resolver(expr, p, PROFUNDIDADE_MAXIMA).resolvido


def test_fatoracao_grau_alto_nao_trava():
    for grau in (1000, 500):
        inicio = time.perf_counter()
        r = _resolver(f"(x^{grau}-1)/(x-1)", "1")
        assert time.perf_counter() - inicio < 2
        assert not r.resolvido


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
    assert not r.resolvido and r.valor is None


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
    assert _resolver("sen(x)/x", "0").validado is None


def test_conferir_com_sympy_aceita_lado_e_ignora_expressao_grande():
    from app.motor.resolvedor import conferir_com_sympy
    assert conferir_com_sympy(1 / x, sp.Integer(0), sp.oo, "+") is True
    assert conferir_com_sympy(1 / x, sp.Integer(0), -sp.oo, "-") is True
    grande = sum(x**k for k in range(400))
    assert conferir_com_sympy(grande, sp.Integer(1), sp.Integer(400)) is None
