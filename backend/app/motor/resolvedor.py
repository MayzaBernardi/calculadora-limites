"""Fluxo principal: decide qual técnica usar e registra os passos."""
from dataclasses import dataclass, field

import sympy as sp

from app.motor import passos
from app.motor.entrada import x
from app.motor.formas import identificar_forma
from app.motor.passos import Passo
from app.motor.tecnicas import fatorar_e_cancelar

PROFUNDIDADE_MAXIMA = 5

# Funções descontínuas: a substituição direta não vale para elas.
FUNCOES_DESCONTINUAS = (sp.floor, sp.ceiling, sp.sign)


@dataclass
class Resultado:
    resolvido: bool
    existe: bool | None = None
    valor: sp.Expr | None = None
    passos: list[Passo] = field(default_factory=list)
    validado: bool | None = None  # conferido com sp.limit (None: não conferido)


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


TAMANHO_MAXIMO_CONFERENCIA = 300  # acima disso (sp.count_ops) não conferimos


def conferir_com_sympy(
    expressao: sp.Expr, ponto: sp.Expr, valor: sp.Expr, lado: str = "+-"
) -> bool | None:
    """Compara o valor com sp.limit. `lado` é "+", "-" ou "+-" (os dois lados,
    padrão); use "+" ou "-" para limites de um lado só. Devolve None se a
    expressão for grande demais ou se o SymPy não conseguir calcular."""
    if sp.count_ops(expressao) > TAMANHO_MAXIMO_CONFERENCIA:
        return None
    try:
        esperado = sp.limit(expressao, x, ponto, lado)
    except Exception:
        return None
    if esperado.has(sp.nan, sp.zoo, sp.AccumBounds):
        return None
    if esperado == valor:
        return True
    if esperado.is_infinite or valor.is_infinite:
        return False
    return bool(sp.simplify(esperado - valor) == 0)


def resolver(expressao: sp.Expr, ponto: sp.Expr, profundidade: int = 0) -> Resultado:
    lista = [passos.passo_funcao_dada(expressao, ponto)]

    if ponto.is_finite:
        valor, motivo = substituir(expressao, ponto)
        if valor is not None:
            lista.append(passos.passo_substituicao_direta(expressao, ponto, valor))
            return Resultado(resolvido=True, existe=True, valor=valor, passos=lista)
        lista.append(passos.passo_substituicao_sem_resultado(expressao, ponto, motivo))

    forma = identificar_forma(expressao, ponto)
    if forma is not None:
        lista.append(passos.passo_forma_indeterminada(expressao, ponto, forma))

    if forma == "0/0" and profundidade < PROFUNDIDADE_MAXIMA:
        fatoracao = fatorar_e_cancelar(expressao, ponto)
        if fatoracao is not None:
            lista.append(passos.passo_fatoracao(
                expressao, ponto, fatoracao.numerador, fatoracao.denominador,
                fatoracao.fator_comum))
            lista.append(passos.passo_cancelamento(
                fatoracao.fator_comum, fatoracao.simplificada,
                fatoracao.numerador, fatoracao.denominador, ponto))
            sub = resolver(fatoracao.simplificada, ponto, profundidade + 1)
            lista.extend(sub.passos[1:])  # o primeiro repete o limite já mostrado
            if sub.resolvido and sub.existe:
                lista.append(passos.passo_resultado(expressao, ponto, sub.valor))
                return Resultado(
                    resolvido=True, existe=True, valor=sub.valor, passos=lista,
                    validado=conferir_com_sympy(expressao, ponto, sub.valor),
                )
            return Resultado(resolvido=False, passos=lista)

    # As próximas etapas (laterais, infinito, L'Hôpital...) entram aqui.
    return Resultado(resolvido=False, passos=lista)
