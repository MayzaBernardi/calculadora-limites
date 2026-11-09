"""Limites laterais, domínio de um lado só e análise de sinal do k/0."""
from dataclasses import dataclass

import sympy as sp

from app.motor.entrada import x
from app.motor.formas import lados_definidos
from app.motor.seguro import executar_com_timeout, limite_seguro

INFINITOS = (sp.oo, -sp.oo)


@dataclass
class Laterais:
    """`esquerda`/`direita` são None quando a função não existe desse lado."""
    esquerda: sp.Expr | None
    direita: sp.Expr | None

    def lados(self) -> list[str]:
        return [l for l, v in (("-", self.esquerda), ("+", self.direita)) if v is not None]

    def valor(self, lado: str) -> sp.Expr | None:
        return self.esquerda if lado == "-" else self.direita


@dataclass
class Conclusao:
    existe: bool
    valor: sp.Expr | None  # None quando o limite não existe


def calcular_laterais(expressao: sp.Expr, ponto: sp.Expr) -> Laterais | None:
    """Limite pela esquerda e pela direita de um ponto finito, olhando só os
    lados onde a função existe. None se algum lado não pôde ser calculado de
    forma confiável (tempo, oscilação, valor sem sentido)."""
    if not ponto.is_finite:
        return None
    lados = lados_definidos(expressao, ponto)
    if not lados:
        return None
    valores = {}
    for lado in lados:
        valor = limite_seguro(expressao, ponto, lado)
        if valor is None or valor.has(sp.nan, sp.zoo, sp.AccumBounds, sp.I):
            return None
        if not (valor in INFINITOS or valor.is_finite):
            return None
        valores[lado] = sp.nsimplify(valor) if valor.has(sp.Float) else valor
    return Laterais(esquerda=valores.get("-"), direita=valores.get("+"))


def concluir(laterais: Laterais) -> Conclusao:
    """Um lado só: vale esse lado. Dois lados: iguais dão o limite; diferentes,
    o limite não existe."""
    lados = laterais.lados()
    if len(lados) == 1:
        return Conclusao(True, laterais.valor(lados[0]))
    if sp.simplify(laterais.esquerda - laterais.direita) == 0 or (
        laterais.esquerda == laterais.direita
    ):
        return Conclusao(True, laterais.direita)
    return Conclusao(False, None)


def _sinal_amostra(expressao: sp.Expr, ponto: sp.Expr, lado: str) -> int | None:
    deslocamento = 1e-6 if lado == "+" else -1e-6
    amostra = sp.Float(float(sp.N(ponto)) + deslocamento, 17)
    valor = complex(expressao.evalf(15, subs={x: amostra}))
    if valor.imag != 0 or valor.real == 0 or valor != valor:
        return None
    return 1 if valor.real > 0 else -1


def sinal_perto(expressao: sp.Expr, ponto: sp.Expr, lado: str) -> int | None:
    """Sinal (+1 ou -1) da expressão logo ao lado do ponto, ou None."""
    ok, sinal = executar_com_timeout(_sinal_amostra, expressao, ponto, lado)
    return sinal if ok else None


@dataclass
class AnaliseSinal:
    lado: str
    sinal_numerador: int
    sinal_denominador: int
    resultado: sp.Expr  # +oo ou -oo


def analisar_sinais(
    expressao: sp.Expr, ponto: sp.Expr, laterais: Laterais
) -> list[AnaliseSinal] | None:
    """Para um k/0 (numerador não nulo, denominador tendendo a 0), explica o
    sinal de cada lado. Devolve None se a análise não se aplica ou se o sinal
    amostrado discorda do limite calculado (nesse caso não explicamos)."""
    num, den = sp.fraction(expressao)
    if den == 1:
        return None
    analises = []
    for lado in laterais.lados():
        valor = laterais.valor(lado)
        if valor not in INFINITOS:
            return None
        sn = sinal_perto(num, ponto, lado)
        sd = sinal_perto(den, ponto, lado)
        if sn is None or sd is None:
            return None
        esperado = sp.oo if sn * sd > 0 else -sp.oo
        if esperado != valor:
            return None
        analises.append(AnaliseSinal(lado, sn, sd, valor))
    return analises or None
