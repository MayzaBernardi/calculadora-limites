"""Identifica a forma indeterminada de um limite (sem aplicar técnica)."""
import sympy as sp

from app.motor.entrada import x

INFINITOS = (sp.oo, -sp.oo)


def _reescrever_exponenciais(parte: sp.Expr) -> sp.Expr:
    """Contorna bug do SymPy: limite de 2**x em -oo sai errado. Usa e^(x ln b)."""
    def trocar(p):
        if p.base.is_number and p.base.is_positive and p.base != sp.E and p.exp.has(x):
            return sp.exp(p.exp * sp.log(p.base))
        return p
    return parte.replace(lambda e: e.is_Pow, trocar)


def limite_da_parte(
    parte: sp.Expr, ponto: sp.Expr, lado: str | None = None
) -> sp.Expr | None:
    """Limite de uma parte (pelo lado "+" ou "-" em ponto finito), ou None se
    não for um número ou ±∞."""
    parte = sp.sympify(parte)
    if parte.is_number and not parte.has(x):
        return parte
    parte = _reescrever_exponenciais(parte)
    try:
        if ponto.is_finite and lado:
            valor = sp.limit(parte, x, ponto, lado)
        else:
            valor = sp.limit(parte, x, ponto)
    except Exception:
        return None
    if valor.has(sp.nan, sp.zoo, sp.AccumBounds) or valor.has(sp.I):
        return None
    if valor in INFINITOS or valor.is_finite:
        return valor
    return None


def _definida_no_lado(expressao: sp.Expr, ponto: sp.Expr, lado: str) -> bool:
    """A expressão assume valores reais logo ao lado do ponto?"""
    try:
        deslocamento = 1e-6 if lado == "+" else -1e-6
        amostra = sp.Float(float(sp.N(ponto)) + deslocamento, 17)
        valor = complex(expressao.evalf(15, subs={x: amostra}))
    except Exception:
        return False
    return valor == valor and abs(valor.imag) < 1e-12 * max(1.0, abs(valor.real))


def _infinito(valor) -> bool:
    return valor in INFINITOS


def _forma_potencia(base: sp.Expr, expoente: sp.Expr, ponto: sp.Expr, lado) -> str | None:
    b = limite_da_parte(base, ponto, lado)
    e = limite_da_parte(expoente, ponto, lado)
    if b is None or e is None:
        return None
    if b == 0 and e == 0:
        return "0^0"
    if b == 1 and _infinito(e):
        return "1^oo"
    if b == sp.oo and e == 0:
        return "oo^0"
    return None


def _forma_quociente(num: sp.Expr, den: sp.Expr, ponto: sp.Expr, lado) -> str | None:
    n = limite_da_parte(num, ponto, lado)
    d = limite_da_parte(den, ponto, lado)
    if n is None or d is None:
        return None
    if n == 0 and d == 0:
        return "0/0"
    if _infinito(n) and _infinito(d):
        return "oo/oo"
    if d == 0 and _infinito(n):
        return "oo/0"
    if d == 0 and n != 0:
        return "k/0"
    return None


def _forma_produto(fatores: tuple, ponto: sp.Expr, lado) -> str | None:
    limites = [limite_da_parte(f, ponto, lado) for f in fatores]
    if any(v is None for v in limites):
        return None
    if any(v == 0 for v in limites) and any(_infinito(v) for v in limites):
        return "0*oo"
    return None


def _forma_soma(termos: tuple, ponto: sp.Expr, lado) -> str | None:
    limites = [limite_da_parte(t, ponto, lado) for t in termos]
    if any(v is None for v in limites):
        return None
    if sp.oo in limites and -sp.oo in limites:
        return "oo-oo"
    return None


def _forma_no_lado(expressao: sp.Expr, ponto: sp.Expr, lado) -> str | None:
    num, den = sp.fraction(expressao)
    if den != 1:
        return _forma_quociente(num, den, ponto, lado)
    if expressao.is_Pow:
        return _forma_potencia(expressao.base, expressao.exp, ponto, lado)
    if expressao.is_Mul:
        return _forma_produto(expressao.args, ponto, lado)
    if expressao.is_Add:
        return _forma_soma(expressao.args, ponto, lado)
    return None


def identificar_forma(expressao: sp.Expr, ponto: sp.Expr) -> str | None:
    """Devolve "0/0", "oo/oo", "k/0", "oo/0", "0*oo", "oo-oo", "1^oo", "0^0",
    "oo^0" ou None. Em ponto finito a forma precisa ser a mesma pelos dois
    lados (considerando só os lados onde a função existe); se os lados
    diferem, devolve None e a análise lateral fica para a Etapa 3."""
    if not ponto.is_finite:
        return _forma_no_lado(expressao, ponto, None)
    formas = {
        _forma_no_lado(expressao, ponto, lado)
        for lado in ("+", "-")
        if _definida_no_lado(expressao, ponto, lado)
    }
    if len(formas) == 1:
        return formas.pop()
    return None
