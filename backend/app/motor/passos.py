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


_EXP_LOG = (
    " Para resolver, usamos f^g = e^(g · ln f)."
)

_FORMAS = {
    "0/0": (
        "Indeterminação 0/0",
        "O numerador e o denominador tendem a 0. Isso é uma indeterminação "
        "0/0: o limite pode ser um número, ∞ ou não existir, então precisamos "
        "simplificar a expressão antes de concluir.",
        r"\frac{0}{0}",
    ),
    "oo/oo": (
        "Indeterminação ∞/∞",
        "O numerador e o denominador crescem sem limite em módulo (∞/∞ e "
        "∞/−∞ também são indeterminações). Precisamos reescrever a expressão "
        "para decidir o valor.",
        r"\frac{\infty}{\infty}",
    ),
    "k/0": (
        "Divisão por zero",
        "O denominador tende a 0 e o numerador tende a um número diferente "
        "de 0. Não é uma indeterminação: o módulo da função cresce sem "
        "limite, e falta analisar o sinal (pelos dois lados) para saber se "
        "o limite existe.",
        r"\frac{k}{0}, \; k \neq 0",
    ),
    "oo/0": (
        "Divisão de infinito por zero",
        "O numerador cresce sem limite e o denominador tende a 0. Não é "
        "uma indeterminação: o módulo da função cresce sem limite, mas "
        "falta analisar os sinais pelos dois lados.",
        r"\frac{\infty}{0}",
    ),
    "0*oo": (
        "Indeterminação 0 · ∞",
        "Um fator tende a 0 e o outro cresce sem limite. Isso é uma "
        "indeterminação 0 · ∞; vamos reescrever o produto como um quociente.",
        r"0 \cdot \infty",
    ),
    "oo-oo": (
        "Indeterminação ∞ − ∞",
        "Os termos tendem a infinitos de sinais opostos. Isso é uma "
        "indeterminação ∞ − ∞; vamos juntar os termos em uma só expressão.",
        r"\infty - \infty",
    ),
    "1^oo": (
        "Indeterminação 1^∞",
        "A base tende a 1 e o expoente cresce sem limite. Isso é uma "
        "indeterminação 1^∞." + _EXP_LOG,
        r"1^{\infty}",
    ),
    "0^0": (
        "Indeterminação 0^0",
        "A base e o expoente tendem a 0. Mesmo que o SymPy avalie 0^0 como "
        "1, no limite isso é uma indeterminação." + _EXP_LOG,
        r"0^{0}",
    ),
    "oo^0": (
        "Indeterminação ∞^0",
        "A base cresce sem limite e o expoente tende a 0. Isso é uma "
        "indeterminação ∞^0." + _EXP_LOG,
        r"\infty^{0}",
    ),
}

_FORMAS_COM_REGRA_EXP = {"1^oo", "0^0", "oo^0"}


def passo_forma_indeterminada(
    expressao: sp.Expr, ponto: sp.Expr, forma: str
) -> Passo:
    titulo, explicacao, forma_tex = _FORMAS[forma]
    latex = f"{limite_tex(expressao, ponto)} \\quad \\text{{forma}} \\quad {forma_tex}"
    if forma in _FORMAS_COM_REGRA_EXP:
        latex += r" \qquad f^{g} = e^{g \ln f}"
    return Passo(titulo=titulo, explicacao=explicacao, latex=latex)


def passo_substituicao_sem_resultado(
    expressao: sp.Expr, ponto: sp.Expr, motivo: str
) -> Passo:
    return Passo(
        titulo="Tentativa de substituição direta",
        explicacao=f"Ao substituir x = {texto_ponto(ponto)}, {motivo}",
        latex=f"{limite_tex(expressao, ponto)} \\to {substituicao_tex(expressao, ponto)}",
    )
