"""Montagem de cada passo da resolução (título, explicação e LaTeX)."""
from dataclasses import dataclass

import sympy as sp

from app.motor.entrada import x

# Símbolo temporário usado para mostrar a substituição sem avaliar a conta.
_MARCADOR = sp.Symbol("Pxqz")


@dataclass
class Passo:
    titulo: str
    explicacao: str
    latex: str


def tex(valor) -> str:
    return sp.latex(valor, ln_notation=True)


def texto_ponto(ponto: sp.Expr) -> str:
    """Ponto em texto simples para as explicações."""
    return sp.sstr(ponto).replace("pi", "π").replace("oo", "∞")


def limite_tex(expressao: sp.Expr, ponto: sp.Expr) -> str:
    return rf"\lim_{{x \to {tex(ponto)}}} {tex(expressao)}"


def substituicao_tex(expressao: sp.Expr, ponto: sp.Expr) -> str:
    """Escreve f(x) com x trocado por (ponto), sem calcular."""
    texto = tex(expressao.xreplace({x: _MARCADOR}))
    if ponto.is_Integer and ponto >= 0 or ponto == sp.pi:
        return texto.replace("Pxqz", tex(ponto))
    return texto.replace("Pxqz", rf"\left({tex(ponto)}\right)")


def passo_funcao_dada(expressao: sp.Expr, ponto: sp.Expr) -> Passo:
    return Passo(
        titulo="Limite a calcular",
        explicacao="Este é o limite pedido.",
        latex=limite_tex(expressao, ponto),
    )


def passo_substituicao_direta(
    expressao: sp.Expr, ponto: sp.Expr, valor: sp.Expr
) -> Passo:
    return Passo(
        titulo="Substituição direta",
        explicacao=(
            f"A função é contínua em x = {texto_ponto(ponto)}, então o limite é "
            "o valor da função nesse ponto: basta substituir x."
        ),
        latex=(
            f"{limite_tex(expressao, ponto)} = {substituicao_tex(expressao, ponto)}"
            f" = {tex(valor)}"
        ),
    )


def passo_substituicao_sem_resultado(
    expressao: sp.Expr, ponto: sp.Expr, motivo: str
) -> Passo:
    return Passo(
        titulo="Tentativa de substituição direta",
        explicacao=f"Ao substituir x = {texto_ponto(ponto)}, {motivo}",
        latex=f"{limite_tex(expressao, ponto)} \\to {substituicao_tex(expressao, ponto)}",
    )
