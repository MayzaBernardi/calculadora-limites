"""Técnicas de resolução. Aqui só se aplica a técnica; os passos ficam em passos.py."""
from dataclasses import dataclass

import sympy as sp

from app.motor.entrada import x

# Acima disso o factor do SymPy fica lento demais (grau 300 leva ~5 s; grau 100 leva menos de 1 s).
GRAU_MAXIMO = 100


@dataclass
class Fatoracao:
    numerador: sp.Expr          # numerador fatorado
    denominador: sp.Expr        # denominador fatorado
    fator_comum: sp.Expr        # fator que zera no ponto e será cancelado
    simplificada: sp.Expr       # expressão depois do cancelamento


def fatorar_e_cancelar(expressao: sp.Expr, ponto: sp.Expr) -> Fatoracao | None:
    """Fatora numerador e denominador de uma função racional e cancela o fator
    comum que se anula em `ponto`. Devolve None se a técnica não se aplica."""
    if not ponto.is_finite:
        return None
    numerador, denominador = sp.fraction(expressao)
    if denominador == 1 and expressao.is_Add:
        # together() já cancela fatores, então só entra quando não há fração explícita
        numerador, denominador = sp.fraction(sp.together(expressao))
    if not (numerador.is_polynomial(x) and denominador.is_polynomial(x)):
        return None
    if denominador.is_number:
        return None
    if max(sp.degree(numerador, x), sp.degree(denominador, x)) > GRAU_MAXIMO:
        return None
    comum = sp.gcd(numerador, denominador)
    if not comum.has(x) or sp.simplify(comum.subs(x, ponto)) != 0:
        return None
    num_fat = sp.factor(numerador)
    den_fat = sp.factor(denominador)
    simplificada = sp.cancel(sp.Mul(num_fat, 1 / den_fat, evaluate=False))
    if simplificada == expressao:
        return None
    # Fator mônico (x - 2 em vez de 2x - 4), mais legível no passo a passo.
    fator = sp.Poly(comum, x).monic().as_expr()
    return Fatoracao(num_fat, den_fat, fator, simplificada)
