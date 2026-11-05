"""Leitura e validação da função e do ponto para onde x tende."""
import re

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

# x é tratado sempre como variável real.
x = sp.Symbol("x", real=True)

TAMANHO_MAXIMO = 200
CARACTERES_PERMITIDOS = re.compile(r"^[0-9a-zA-Zπ∞+\-*/^().,|\s]+$")

TRANSFORMACOES = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

NOMES_CONHECIDOS = {
    "x": x,
    "sen": sp.sin,
    "sin": sp.sin,
    "cos": sp.cos,
    "tg": sp.tan,
    "tan": sp.tan,
    "arcsen": sp.asin,
    "arccos": sp.acos,
    "arctg": sp.atan,
    "ln": sp.log,
    "log": sp.log,
    "exp": sp.exp,
    "raiz": sp.sqrt,
    "sqrt": sp.sqrt,
    "abs": sp.Abs,
    "piso": sp.floor,
    "floor": sp.floor,
    "teto": sp.ceiling,
    "ceil": sp.ceiling,
    "pi": sp.pi,
    "e": sp.E,
}

# Únicas classes expostas ao eval do parse_expr (ele precisa delas por dentro).
GLOBAIS_SEGUROS = {
    "Integer": sp.Integer,
    "Float": sp.Float,
    "Rational": sp.Rational,
    "Symbol": sp.Symbol,
}

PONTOS_INFINITO_POSITIVO = {"infinito", "+infinito", "inf", "+inf", "oo", "+oo", "∞", "+∞"}
PONTOS_INFINITO_NEGATIVO = {"-infinito", "-inf", "-oo", "-∞"}


class ErroEntrada(ValueError):
    """Entrada inválida; a mensagem é mostrada ao usuário."""


def _converter(texto: str, descricao: str) -> sp.Expr:
    texto = texto.replace("π", "pi")
    # |u| vira abs(u) (barras não aninhadas).
    texto = re.sub(r"\|([^|]*)\|", r"abs(\1)", texto)
    if "|" in texto:
        raise ErroEntrada("As barras de módulo | | estão mal fechadas.")
    try:
        return parse_expr(
            texto,
            local_dict=dict(NOMES_CONHECIDOS),
            global_dict=dict(GLOBAIS_SEGUROS),
            transformations=TRANSFORMACOES,
            evaluate=True,
        )
    except Exception as erro:
        raise ErroEntrada(
            f"Não consegui entender {descricao}: «{texto}». "
            "Confira parênteses, operadores e nomes de funções."
        ) from erro


def _validar_texto(texto: str, descricao: str) -> str:
    if not isinstance(texto, str) or not texto.strip():
        raise ErroEntrada(f"Informe {descricao}.")
    texto = texto.strip()
    if len(texto) > TAMANHO_MAXIMO:
        raise ErroEntrada(f"{descricao.capitalize()} é longa demais.")
    if not CARACTERES_PERMITIDOS.match(texto):
        raise ErroEntrada(f"{descricao.capitalize()} contém caracteres inválidos.")
    return texto


def ler_funcao(texto: str) -> sp.Expr:
    """Converte o texto digitado em uma expressão do SymPy na variável x."""
    texto = _validar_texto(texto, "a função")
    expressao = _converter(texto, "a função")
    if not isinstance(expressao, sp.Expr):
        raise ErroEntrada("A função informada não é uma expressão matemática.")
    desconhecidos = expressao.free_symbols - {x}
    if desconhecidos:
        nomes = ", ".join(sorted(str(s) for s in desconhecidos))
        raise ErroEntrada(
            f"A função deve usar apenas a variável x (encontrei também: {nomes})."
        )
    return expressao


def ler_ponto(texto: str) -> sp.Expr:
    """Converte o valor para onde x tende: número, oo ou -oo."""
    texto = _validar_texto(texto, "o valor para onde x tende")
    normalizado = texto.lower().replace(" ", "")
    if normalizado in PONTOS_INFINITO_POSITIVO:
        return sp.oo
    if normalizado in PONTOS_INFINITO_NEGATIVO:
        return -sp.oo
    ponto = _converter(texto, "o valor para onde x tende")
    if not isinstance(ponto, sp.Expr) or ponto.free_symbols or not ponto.is_real:
        raise ErroEntrada(
            "O valor para onde x tende deve ser um número real, infinito ou -infinito."
        )
    if ponto.has(sp.Float):
        ponto = sp.nsimplify(ponto, rational=True)
    return ponto
