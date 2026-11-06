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


def tex_ordenado(valor) -> str:
    """Como tex(), mas uma soma sai com os termos na ordem de `valor.args`."""
    if not valor.is_Add:
        return tex(valor)
    texto = tex(valor.args[0])
    for termo in valor.args[1:]:
        if termo.could_extract_minus_sign():
            texto += f" - {tex(-termo)}"
        else:
            texto += f" + {tex(termo)}"
    return texto


def texto_ponto(ponto: sp.Expr) -> str:
    """Ponto em texto simples para as explicações."""
    return sp.sstr(ponto).replace("pi", "π").replace("oo", "∞").replace("sqrt(", "√(")


def limite_tex(expressao: sp.Expr, ponto: sp.Expr) -> str:
    corpo = tex(expressao)
    if expressao.is_Add:
        corpo = rf"\left({corpo}\right)"
    return rf"\lim_{{x \to {tex(ponto)}}} {corpo}"


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


def _texto_expr(expr: sp.Expr) -> str:
    return texto_ponto(expr).replace("**", "^").replace("*", " · ")


def passo_fatoracao(
    expressao: sp.Expr, ponto: sp.Expr, num_fat: sp.Expr, den_fat: sp.Expr,
    fator: sp.Expr,
) -> Passo:
    return Passo(
        titulo="Fatoração",
        explicacao=(
            "A substituição deu 0/0, então numerador e denominador se anulam no "
            "ponto e devem ter um fator em comum. Fatorando numerador e "
            f"denominador, aparece o fator {_texto_expr(fator)} nos dois."
        ),
        latex=(
            f"{limite_tex(expressao, ponto)} = \\lim_{{x \\to {tex(ponto)}}} "
            rf"\frac{{{tex(num_fat)}}}{{{tex(den_fat)}}}"
        ),
    )


def passo_cancelamento(
    fator: sp.Expr, simplificada: sp.Expr, num_fat: sp.Expr, den_fat: sp.Expr,
    ponto: sp.Expr,
) -> Passo:
    return Passo(
        titulo="Cancelamento do fator comum",
        explicacao=(
            f"Cancelamos o fator {_texto_expr(fator)} do numerador com o do "
            "denominador. Isso é permitido porque x tende ao ponto, mas nunca é "
            "igual a ele; logo esse fator é diferente de zero e o limite não muda."
        ),
        latex=(
            rf"\lim_{{x \to {tex(ponto)}}} \frac{{{tex(num_fat)}}}{{{tex(den_fat)}}}"
            f" = {limite_tex(simplificada, ponto)}"
        ),
    )


def passo_resultado(expressao: sp.Expr, ponto: sp.Expr, valor: sp.Expr) -> Passo:
    return Passo(
        titulo="Resultado",
        explicacao=(
            f"O limite quando x tende a {texto_ponto(ponto)} vale {texto_ponto(valor)}."
        ),
        latex=f"{limite_tex(expressao, ponto)} = {tex(valor)}",
    )


def _com_parenteses(expr: sp.Expr) -> str:
    return tex(expr) if expr.is_Atom else rf"\left({tex(expr)}\right)"


def passo_conjugado(r) -> Passo:
    explicacao = (
        f"Há uma raiz no {r.alvo}, e a substituição deu 0/0. Para eliminar a "
        f"raiz, usamos o conjugado de {_texto_expr(r.com_raiz_exib)}: a mesma "
        f"expressão com o sinal entre os dois termos trocado, "
        f"{_texto_expr(r.conjugado_exib)}. Vamos multiplicar o numerador e o "
        "denominador por ele; isso não muda o valor, pois estamos "
        "multiplicando a fração por 1."
    )
    if r.raiz_nos_dois_lados:
        explicacao += (
            " Como a outra parte da fração também tem raiz, depois de simplificar "
            "repetimos o processo com ela."
        )
    return Passo(
        titulo="Conjugado",
        explicacao=explicacao,
        latex=(
            rf"{tex_ordenado(r.com_raiz_exib)} \;\longrightarrow\; "
            rf"{tex_ordenado(r.conjugado_exib)}"
        ),
    )


def passo_multiplicacao_conjugado(expressao: sp.Expr, ponto: sp.Expr, r) -> Passo:
    n, d = sp.fraction(expressao)
    c = tex_ordenado(r.conjugado_exib)
    quadrado_p, quadrado_q = r.primeiro**2, r.segundo**2
    identidade = (
        rf"\left({tex_ordenado(r.com_raiz_exib)}\right)\left({c}\right) = "
        rf"{_com_parenteses(r.primeiro)}^{{2}} - {_com_parenteses(r.segundo)}^{{2}}"
        rf" = {_com_parenteses(quadrado_p)} - {_com_parenteses(quadrado_q)}"
        rf" = {tex(r.produto)}"
    )
    multiplicacao = (
        f"{limite_tex(expressao, ponto)} = "
        rf"\lim_{{x \to {tex(ponto)}}} \frac{{{tex(n)}}}{{{tex(d)}}}"
        rf" \cdot \frac{{{c}}}{{{c}}}"
    )
    return Passo(
        titulo="Multiplicação pelo conjugado",
        explicacao=(
            "Usamos o produto notável (a − b)(a + b) = a² − b². Assim o "
            f"{r.alvo} multiplicado pelo conjugado vira {_texto_expr(r.produto)}, "
            "sem raiz, porque o quadrado de uma raiz quadrada é o que está dentro dela."
        ),
        latex=rf"\begin{{gathered}}{multiplicacao} \\ {identidade}\end{{gathered}}",
    )


def passo_simplificacao_racionalizacao(
    expressao: sp.Expr, ponto: sp.Expr, r
) -> Passo:
    if r.fator_cancelado is not None:
        explicacao = (
            f"O fator {_texto_expr(r.fator_cancelado)} aparece no numerador e no "
            "denominador e se anula no ponto. Como x se aproxima do ponto sem "
            "nunca ser igual a ele, esse fator é diferente de zero e podemos "
            "cancelá-lo sem mudar o limite."
        )
    else:
        explicacao = (
            "Reorganizamos o produto sem cancelar nada ainda: a raiz que "
            "atrapalhava saiu desta parte da fração."
        )
    return Passo(
        titulo="Simplificação",
        explicacao=explicacao,
        latex=(
            rf"\lim_{{x \to {tex(ponto)}}} \frac{{{tex(r.numerador)}}}{{{tex(r.denominador)}}}"
            f" = {limite_tex(r.simplificada, ponto)}"
        ),
    )


def passo_tecnica_sem_conclusao(conferencia_falhou: bool) -> Passo:
    if conferencia_falhou:
        return Passo(
            titulo="Conferência não coincidiu",
            explicacao=(
                "Ao conferir o resultado com um cálculo independente, os valores "
                "não coincidiram. Por isso não afirmamos esse resultado: não "
                "conseguimos concluir o limite por esta técnica."
            ),
            latex=r"\text{resultado não confirmado}",
        )
    return Passo(
        titulo="Não conseguimos concluir",
        explicacao=(
            "A técnica aplicada não levou a um valor para o limite, então não "
            "conseguimos concluir por este caminho."
        ),
        latex=r"\text{sem conclusão}",
    )
