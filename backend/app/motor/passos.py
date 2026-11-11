"""Montagem de cada passo da resolução (título, explicação e LaTeX)."""
import re
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
    return sp.sstr(ponto).replace("pi", "π").replace("oo", "∞").replace("sqrt(", "√(").replace("log(", "ln(")


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
    if expressao.has(x):
        conta = f"{substituicao_tex(expressao, ponto)} = {tex(valor)}"
    else:
        conta = tex(valor)  # constante: não há o que substituir
    return Passo(
        titulo="Substituição direta",
        explicacao=(
            f"A função é contínua em x = {texto_ponto(ponto)}, então o limite é "
            "o valor da função nesse ponto: basta substituir x."
        ),
        latex=f"{limite_tex(expressao, ponto)} = {conta}",
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
    texto = texto_ponto(expr).replace("**", "^").replace("*", " · ")
    texto = texto.replace("sin(", "sen(").replace("tan(", "tg(")
    return re.sub(r"(sen|tg)\(([^()]*)\)\^2", r"\1²(\2)", texto)


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


def passo_limite_fundamental(bloco, ponto: sp.Expr) -> Passo:
    return Passo(
        titulo="Limite fundamental",
        explicacao=(
            f"No {bloco.lado} aparece {_texto_expr(bloco.g)}, que lembra um limite "
            f"fundamental com u = {_texto_expr(bloco.u)}. Isso só vale se u tender "
            f"a 0: quando x tende a {texto_ponto(ponto)}, u = {_texto_expr(bloco.u)} "
            "tende a 0, então podemos usar o limite fundamental abaixo."
        ),
        latex=(
            rf"{bloco.formula}, \quad u = {tex(bloco.u)}, \quad "
            rf"\lim_{{x \to {tex(ponto)}}} {_com_parenteses(bloco.u)} = 0"
        ),
    )


def _fator_fundamental_tex(f) -> str:
    n = next((b for b in f.blocos if b.lado == "numerador"), None)
    d = next((b for b in f.blocos if b.lado == "denominador"), None)
    frac_n = rf"\frac{{{tex(n.g)}}}{{{tex(n.h)}}}" if n else None
    frac_d = rf"\frac{{{tex(d.g)}}}{{{tex(d.h)}}}" if d else None
    if n and d:
        return rf"\frac{{{frac_n}}}{{{frac_d}}}"
    if n:
        return frac_n
    return rf"\frac{{1}}{{{frac_d}}}"


def passo_ajuste_fundamental(expressao: sp.Expr, ponto: sp.Expr, f) -> Passo:
    return Passo(
        titulo="Ajuste algébrico",
        explicacao=(
            "Multiplicamos e dividimos pelo que falta para que apareça exatamente "
            "o limite fundamental (u no denominador, igual ao argumento). O que "
            "sobra fora dele é uma expressão mais simples."
        ),
        latex=(
            f"{limite_tex(expressao, ponto)} = "
            rf"\lim_{{x \to {tex(ponto)}}} {_fator_fundamental_tex(f)} \cdot "
            rf"{_com_parenteses(f.resto) if f.resto.is_Add else tex(f.resto)}"
        ),
    )


def passo_produto_de_limites(expressao: sp.Expr, ponto: sp.Expr, f) -> Passo:
    quociente = f.valor_denominador is not None
    explicacao = (
        "O limite de um produto é o produto dos limites, quando cada um existe."
    )
    if quociente:
        explicacao = (
            "Usamos as regras do produto e do quociente de limites: o limite de "
            "um produto (ou quociente) é o produto (ou quociente) dos limites, "
            "desde que existam e o do denominador não seja 0. Aqui o limite do "
            f"bloco do denominador vale {texto_ponto(f.valor_denominador)}, "
            "que é diferente de 0."
        )
    explicacao += (
        f" A parte do limite fundamental vale {texto_ponto(f.fator)}; falta "
        "calcular o limite do que sobrou."
    )
    resto = _com_parenteses(f.resto) if f.resto.is_Add else tex(f.resto)
    return Passo(
        titulo=("Limite do produto e do quociente" if quociente
                else "Limite do produto"),
        explicacao=explicacao,
        latex=(
            rf"{limite_tex(expressao, ponto)} = {tex(f.fator)} \cdot "
            rf"\lim_{{x \to {tex(ponto)}}} {resto}"
        ),
    )


def passo_termo_dominante(expressao: sp.Expr, ponto: sp.Expr, d) -> Passo:
    """d: TermoDominante (ver tecnicas.py)."""
    a = texto_ponto(ponto)
    if d.grau == 0:
        return Passo(
            titulo="Função constante",
            explicacao=(
                "Esta expressão não depende de x: é uma função constante. "
                "Não importa para onde x tende, o valor não muda, então o "
                f"limite é o próprio valor: {_valor_texto(d.valor)}."
            ),
            latex=f"{limite_tex(expressao, ponto)} = {tex(d.valor)}",
        )
    paridade = "par" if d.grau % 2 == 0 else "ímpar"
    sinal_coef = "positivo" if d.coeficiente_lider.is_positive else "negativo"
    if d.termo == d.polinomio:
        # Não há termos de grau menor: a expressão já é só esse termo, então
        # repetir "lim termo = lim termo" seria uma afirmação vazia.
        explicacao = (
            f"Esta expressão já é só um termo, {_texto_expr(d.termo)}: não há "
            "outros termos com os quais compará-lo. Quando x tende "
            f"a {a}, o que decide o resultado é o grau e o sinal do "
            f"coeficiente. Aqui o grau é {d.grau} ({paridade}) e o "
            f"coeficiente é {sinal_coef} ({_texto_expr(d.coeficiente_lider)}); "
            f"combinando isso com x tendendo a {a}, o termo tende a "
            f"{_valor_texto(d.valor)}."
        )
        latex = f"{limite_tex(expressao, ponto)} = {tex(d.valor)}"
    else:
        explicacao = (
            f"Quando x tende a {a}, o termo de maior grau do polinômio, "
            f"{_texto_expr(d.termo)}, domina o comportamento da função: os "
            "termos de grau menor crescem muito mais devagar e ficam "
            "desprezíveis em comparação com ele. Por isso o limite do "
            "polinômio é igual ao limite do seu termo de maior grau. Aqui o "
            f"grau é {d.grau} ({paridade}) e o coeficiente líder é "
            f"{sinal_coef} ({_texto_expr(d.coeficiente_lider)}); combinando "
            f"isso com x tendendo a {a}, esse termo tende a "
            f"{_valor_texto(d.valor)}."
        )
        latex = (
            f"{limite_tex(expressao, ponto)} = "
            rf"\lim_{{x \to {tex(ponto)}}} {tex(d.termo)} = {tex(d.valor)}"
        )
    return Passo(
        titulo="Termo de maior grau domina",
        explicacao=explicacao,
        latex=latex,
    )


def passo_divisao_maior_potencia(expressao: sp.Expr, ponto: sp.Expr, d) -> Passo:
    """d: DivisaoMaiorPotencia (ver tecnicas.py)."""
    potencia = x**d.grau_denominador
    explicacao = (
        "A forma é ∞/∞: tanto o numerador quanto o denominador crescem sem "
        "limite, então a substituição direta não decide o resultado. A "
        "técnica padrão é dividir os dois pela maior potência de x que "
        f"aparece no denominador, {_texto_expr(potencia)}, e simplificar "
        "cada termo; isso não muda o valor da fração, pois é o mesmo que "
        "multiplicar por 1 (1 dividido por ele mesmo)."
    )
    latex = (
        f"{limite_tex(expressao, ponto)} = "
        rf"\lim_{{x \to {tex(ponto)}}} "
        rf"\frac{{{_com_parenteses(d.numerador)} \;/\; {tex(potencia)}}}"
        rf"{{{_com_parenteses(d.denominador)} \;/\; {tex(potencia)}}}"
        rf" = \lim_{{x \to {tex(ponto)}}} "
        rf"\frac{{{tex(d.numerador_dividido)}}}{{{tex(d.denominador_dividido)}}}"
    )
    return Passo(titulo="Divisão pela maior potência", explicacao=explicacao, latex=latex)


def passo_conclusao_divisao_maior_potencia(
    expressao: sp.Expr, ponto: sp.Expr, d
) -> Passo:
    """d: DivisaoMaiorPotencia (ver tecnicas.py). Explica, termo a termo, por
    que cada parcela c/x^k (k > 0) desaparece e o que sobra decide o valor."""
    a = texto_ponto(ponto)
    frac = rf"\frac{{{tex(d.numerador_dividido)}}}{{{tex(d.denominador_dividido)}}}"
    if d.caso == "menor":
        explicacao = (
            f"Quando x tende a {a}, todo termo da forma c/x^k (com k > 0) tende "
            "a 0. Assim, o numerador tende a 0, e o denominador tende ao seu "
            f"termo constante, {_texto_expr(d.coeficiente_denominador)}, que é "
            "diferente de 0. Zero dividido por um número diferente de zero é 0."
        )
        latex = rf"{frac} \;\longrightarrow\; \frac{{0}}{{{tex(d.coeficiente_denominador)}}} = 0"
    elif d.caso == "igual":
        explicacao = (
            f"Quando x tende a {a}, todo termo da forma c/x^k (com k > 0) tende "
            "a 0, e sobra só o termo constante de cada lado: o numerador tende "
            f"a {_texto_expr(d.coeficiente_numerador)}, e o denominador tende a "
            f"{_texto_expr(d.coeficiente_denominador)}. O limite é a razão entre "
            "os coeficientes líderes do numerador e do denominador."
        )
        latex = (
            rf"{frac} \;\longrightarrow\; "
            rf"\frac{{{tex(d.coeficiente_numerador)}}}{{{tex(d.coeficiente_denominador)}}}"
            rf" = {tex(d.valor)}"
        )
    else:
        grau_restante = d.grau_numerador - d.grau_denominador
        paridade = "par" if grau_restante % 2 == 0 else "ímpar"
        razao = d.coeficiente_numerador / d.coeficiente_denominador
        sinal_razao = "positiva" if razao.is_positive else "negativa"
        termo_que_sobra = d.coeficiente_numerador * x**grau_restante
        explicacao = (
            f"Quando x tende a {a}, os termos da forma c/x^k (com k > 0) tendem "
            f"a 0, mas o numerador ainda tem o termo {_texto_expr(termo_que_sobra)}, "
            "que não desaparece: continua crescendo sem limite, porque o grau "
            f"que restou ({grau_restante}) é maior que 0. O denominador tende a "
            f"{_texto_expr(d.coeficiente_denominador)} (um número fixo, diferente "
            "de 0). Dividir algo que cresce sem limite por um número fixo ainda "
            "cresce sem limite; o sinal do resultado vem da razão entre os "
            f"coeficientes líderes, que é {sinal_razao} ({_texto_expr(razao)}), "
            f"combinada com o grau que restou ser {paridade} e x tender a {a}."
        )
        latex = rf"{frac} \;\longrightarrow\; {tex(d.valor)}"
    return Passo(
        titulo="Limite termo a termo",
        explicacao=explicacao,
        latex=latex,
    )


def passo_tecnica_sem_conclusao(motivo: str | bool) -> Passo:
    """motivo: "divergiu" (ou True), "nao_confirmado" ou "sem_conclusao"."""
    if motivo is True:
        motivo = "divergiu"
    if motivo == "divergiu":
        return Passo(
            titulo="Conferência não coincidiu",
            explicacao=(
                "Ao conferir o resultado com um cálculo independente, os valores "
                "não coincidiram. Por isso não afirmamos esse resultado: não "
                "conseguimos concluir o limite por esta técnica."
            ),
            latex=r"\text{resultado não confirmado}",
        )
    if motivo == "nao_confirmado":
        return Passo(
            titulo="Não conseguimos concluir",
            explicacao=(
                "Não foi possível confirmar o resultado com um cálculo independente "
                "(o cálculo demorou demais ou foi inconclusivo). Por isso não "
                "afirmamos esse valor: não conseguimos concluir o limite."
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


def limite_lateral_tex(expressao: sp.Expr, ponto: sp.Expr, lado: str) -> str:
    corpo = tex(expressao)
    if expressao.is_Add:
        corpo = rf"\left({corpo}\right)"
    sinal = "-" if lado == "-" else "+"
    return rf"\lim_{{x \to {tex(ponto)}^{{{sinal}}}}} {corpo}"


def _nome_lado(lado: str) -> str:
    return "esquerda" if lado == "-" else "direita"


def _valor_texto(valor: sp.Expr) -> str:
    return texto_ponto(valor).replace("oo", "∞")


def passo_laterais(expressao: sp.Expr, ponto: sp.Expr, laterais) -> Passo:
    """Mostra o limite de cada lado (e avisa quando a função só existe de um)."""
    a = texto_ponto(ponto)
    linhas, partes = [], []
    for lado in ("-", "+"):
        valor = laterais.valor(lado)
        if valor is None:
            partes.append(
                f"Pela {_nome_lado(lado)} (x → {a}{'⁻' if lado == '-' else '⁺'}) a "
                "função não está definida nos reais, então esse lado não conta."
            )
            continue
        linhas.append(f"{limite_lateral_tex(expressao, ponto, lado)} = {tex(valor)}")
        partes.append(
            f"Pela {_nome_lado(lado)} (x → {a}{'⁻' if lado == '-' else '⁺'}) o limite é "
            f"{_valor_texto(valor)}."
        )
    return Passo(
        titulo="Limites laterais",
        explicacao=(
            "Para saber se o limite existe, olhamos os dois lados: x se aproximando "
            f"de {a} por valores menores (esquerda, x → {a}⁻) e por valores maiores "
            f"(direita, x → {a}⁺). " + " ".join(partes)
        ),
        latex=r" \qquad ".join(linhas),
    )


def _palavra_sinal(sinal: int) -> str:
    return "positivo" if sinal > 0 else "negativo"


def passo_analise_de_sinal(expressao: sp.Expr, ponto: sp.Expr, analises) -> Passo:
    """k/0: o denominador vai a 0, então o quociente cresce sem limite; o sinal
    de cada lado decide se vai a +∞ ou a −∞."""
    a = texto_ponto(ponto)
    frases, linhas = [], []
    for an in analises:
        simbolo = "⁻" if an.lado == "-" else "⁺"
        resultado = "+∞" if an.resultado == sp.oo else "−∞"
        frases.append(
            f"Pela {_nome_lado(an.lado)} (x → {a}{simbolo}), o numerador é "
            f"{_palavra_sinal(an.sinal_numerador)} e o denominador é "
            f"{_palavra_sinal(an.sinal_denominador)} (e tende a 0), então o "
            f"quociente é {_palavra_sinal(an.sinal_numerador * an.sinal_denominador)} "
            f"e cresce sem limite: {resultado}."
        )
        linhas.append(
            f"{limite_lateral_tex(expressao, ponto, an.lado)} = {tex(an.resultado)}"
        )
    return Passo(
        titulo="Análise de sinal (divisão por zero)",
        explicacao=(
            "O denominador tende a 0 e o numerador não, então o quociente fica "
            "cada vez maior em módulo. O que falta é o sinal, que depende do lado. "
            + " ".join(frases)
        ),
        latex=r" \qquad ".join(linhas),
    )


def passo_conclusao_laterais(
    expressao: sp.Expr, ponto: sp.Expr, laterais, conclusao
) -> Passo:
    a = texto_ponto(ponto)
    lados = laterais.lados()
    if len(lados) == 1:
        lado = lados[0]
        return Passo(
            titulo="Função definida de um lado só",
            explicacao=(
                f"A função só existe à {_nome_lado(lado)} de {a}, então o limite é "
                f"o limite desse lado: {_valor_texto(conclusao.valor)}."
            ),
            latex=f"{limite_tex(expressao, ponto)} = {tex(conclusao.valor)}",
        )
    if conclusao.existe:
        return Passo(
            titulo="Os laterais coincidem",
            explicacao=(
                "Os limites pela esquerda e pela direita são iguais, então o limite "
                f"existe e vale {_valor_texto(conclusao.valor)}."
            ),
            latex=f"{limite_tex(expressao, ponto)} = {tex(conclusao.valor)}",
        )
    return Passo(
        titulo="Os laterais são diferentes: o limite não existe",
        explicacao=(
            f"Pela esquerda o limite é {_valor_texto(laterais.esquerda)} e pela direita "
            f"é {_valor_texto(laterais.direita)}. Como são diferentes, o limite "
            f"quando x tende a {a} não existe."
        ),
        latex=(
            f"{tex(laterais.esquerda)} \\neq {tex(laterais.direita)} "
            r"\;\Rightarrow\; \text{o limite não existe}"
        ),
    )
