"""Pontos (x, y) do gráfico, amostrados com segurança (NumPy + timeout)."""
import numpy as np
import sympy as sp

from app.motor.entrada import x
from app.motor.seguro import executar_com_timeout

# Ímpar de propósito: com uma janela simétrica em torno do ponto, garante que
# o próprio ponto cai exatamente na malha amostrada (vira o x do meio).
QUANTIDADE_PADRAO = 201
METADE_JANELA_FINITA = 5.0
# x -> +infinito: a janela mostra mais do lado positivo (onde o limite
# importa), mas ainda com um pouco do lado negativo para dar contexto.
JANELA_INFINITO_POSITIVO = (-10.0, 30.0)
JANELA_INFINITO_NEGATIVO = (-30.0, 10.0)
TEMPO_MAXIMO = 5.0
TOLERANCIA_IMAGINARIA = 1e-9


def _janela(ponto: sp.Expr) -> tuple[float, float]:
    if ponto == sp.oo:
        return JANELA_INFINITO_POSITIVO
    if ponto == -sp.oo:
        return JANELA_INFINITO_NEGATIVO
    valor = float(ponto)
    return valor - METADE_JANELA_FINITA, valor + METADE_JANELA_FINITA


def _avaliar_um(funcao, valor: float) -> float | None:
    try:
        y = funcao(valor)
    except (ZeroDivisionError, OverflowError, ValueError, TypeError):
        return None
    try:
        y = complex(y)
    except TypeError:
        return None
    if y.real != y.real:  # nan
        return None
    if abs(y.imag) > TOLERANCIA_IMAGINARIA * max(1.0, abs(y.real)):
        return None  # valor não real: fora do domínio real da função
    if not np.isfinite(y.real):
        return None
    return float(y.real)


def _gerar_pontos(
    expressao: sp.Expr, inicio: float, fim: float, quantidade: int
) -> list[tuple[float, float | None]]:
    valores_x = np.linspace(inicio, fim, quantidade)
    funcao = sp.lambdify(x, expressao, modules=["numpy"])
    with np.errstate(all="ignore"):
        pontos = [(float(vx), _avaliar_um(funcao, vx)) for vx in valores_x]
    return pontos


def calcular_pontos(
    expressao: sp.Expr, ponto: sp.Expr, quantidade: int = QUANTIDADE_PADRAO
) -> list[tuple[float, float | None]]:
    """Amostra f(x) num intervalo em torno do ponto pedido (ou numa janela
    fixa, se x -> ±infinito). Pontos fora do domínio real vêm com y=None,
    para o frontend não ligar os dois lados de uma assíntote."""
    inicio, fim = _janela(ponto)
    ok, pontos = executar_com_timeout(
        _gerar_pontos, expressao, inicio, fim, quantidade, tempo=TEMPO_MAXIMO
    )
    if not ok:
        # Não deu para avaliar a tempo: ainda devolve a malha de x, sem y.
        valores_x = np.linspace(inicio, fim, quantidade)
        return [(float(vx), None) for vx in valores_x]
    return pontos
