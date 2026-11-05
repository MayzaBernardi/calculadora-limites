import pytest
import sympy as sp

from app.motor.entrada import ErroEntrada, ler_funcao, ler_ponto, x
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
        ("(x^2-4)/(x-2)", "2"),   # 0/0
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
