"""Fluxo principal: decide qual técnica usar e registra os passos."""
from dataclasses import dataclass, field

import sympy as sp

from app.motor import passos
from app.motor.entrada import x
from app.motor.passos import Passo

# Funções descontínuas: a substituição direta não vale para elas.
FUNCOES_DESCONTINUAS = (sp.floor, sp.ceiling, sp.sign)


@dataclass
class Resultado:
    resolvido: bool
    existe: bool | None = None
    valor: sp.Expr | None = None
    passos: list[Passo] = field(default_factory=list)


def _tem_zero_elevado_a_zero(expressao: sp.Expr, ponto: sp.Expr) -> bool:
    """O SymPy diz 0**0 = 1, mas para limites 0^0 é indeterminação."""
    for potencia in expressao.atoms(sp.Pow):
        base = potencia.base.subs(x, ponto)
        expoente = potencia.exp.subs(x, ponto)
        if base == 0 and expoente == 0:
            return True
    return False


def substituir(expressao: sp.Expr, ponto: sp.Expr) -> tuple[sp.Expr | None, str]:
    """Tenta f(ponto). Devolve (valor, "") ou (None, motivo da falha)."""
    if expressao.has(*FUNCOES_DESCONTINUAS):
        return None, "a função tem saltos (piso, teto ou sinal), então não vale substituir."
    if _tem_zero_elevado_a_zero(expressao, ponto):
        return None, "aparece 0^0, que é uma indeterminação."
    valor = sp.simplify(expressao.subs(x, ponto))
    if valor.has(sp.nan):
        return None, "aparece uma indeterminação (como 0/0)."
    if valor.has(sp.zoo, sp.oo, -sp.oo):
        return None, "aparece uma divisão por zero ou um valor infinito."
    if valor.has(sp.I) or valor.is_real is False:
        return None, "o ponto está fora do domínio da função (resultado não real)."
    return valor, ""


def resolver(expressao: sp.Expr, ponto: sp.Expr) -> Resultado:
    lista = [passos.passo_funcao_dada(expressao, ponto)]

    if ponto.is_finite:
        valor, motivo = substituir(expressao, ponto)
        if valor is not None:
            lista.append(passos.passo_substituicao_direta(expressao, ponto, valor))
            return Resultado(resolvido=True, existe=True, valor=valor, passos=lista)
        lista.append(passos.passo_substituicao_sem_resultado(expressao, ponto, motivo))

    # As próximas etapas (0/0, laterais, infinito...) entram aqui.
    return Resultado(resolvido=False, passos=lista)
