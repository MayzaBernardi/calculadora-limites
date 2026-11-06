"""Cálculo de limites com sp.limit protegido por tempo.

Mecanismo: o sp.limit roda em um processo filho criado com fork
(multiprocessing, contexto "fork") e o resultado volta por um pipe. Se passar
do tempo, o filho é morto. Escolhi processo e não thread porque uma thread não
pode ser interrompida, e não escolhi SIGALRM porque ele só funciona na thread
principal (o FastAPI executa rotas síncronas em threads). O fork existe só em
Linux/macOS; sem ele, o limite roda direto, sem proteção de tempo.
A API da Etapa 6 deve usar esta mesma função.
"""
import multiprocessing

import sympy as sp

from app.motor.entrada import x

TEMPO_MAXIMO = 3.0  # segundos por limite


def _reescrever_exponenciais(expr: sp.Expr) -> sp.Expr:
    """Contorna bug do SymPy: limite de 2**x em -oo sai errado. Usa e^(x ln b)."""
    def trocar(p):
        if p.base.is_number and p.base.is_positive and p.base != sp.E and p.exp.has(x):
            return sp.exp(p.exp * sp.log(p.base))
        return p
    return expr.replace(lambda e: e.is_Pow, trocar)


def _reescrever_raizes_de_quadrados(expr: sp.Expr) -> sp.Expr:
    """sqrt(polinômio quadrado perfeito) vira Abs(...): sqrt(x^2-2x+1) = |x-1|.
    O SymPy trava com a forma original."""
    def trocar(p):
        if p.exp != sp.Rational(1, 2) or not p.base.has(x):
            return p
        if not p.base.is_polynomial(x) or sp.degree(p.base, x) > 10:
            return p
        fatorado = sp.factor(p.base)
        if fatorado.is_Pow and fatorado.exp == 2:
            return sp.Abs(fatorado.base)
        return p
    return expr.replace(lambda e: e.is_Pow, trocar)


def preparar_para_limite(expr: sp.Expr) -> sp.Expr:
    return _reescrever_raizes_de_quadrados(_reescrever_exponenciais(expr))


def _trabalhador(expr, ponto, direcao, conexao):
    try:
        if direcao is None:
            valor = sp.limit(expr, x, ponto)
        else:
            valor = sp.limit(expr, x, ponto, direcao)
        conexao.send(("ok", valor))
    except BaseException as erro:  # noqa: BLE001 - qualquer falha vira None
        conexao.send(("erro", repr(erro)))
    finally:
        conexao.close()


def limite_seguro(
    expr: sp.Expr, ponto: sp.Expr, direcao: str | None = None,
    tempo: float = TEMPO_MAXIMO,
) -> sp.Expr | None:
    """sp.limit(expr, x, ponto, direcao) ou None se falhar ou passar do tempo."""
    expr = preparar_para_limite(sp.sympify(expr))
    try:
        contexto = multiprocessing.get_context("fork")
    except ValueError:
        try:
            return sp.limit(expr, x, ponto, direcao) if direcao else sp.limit(expr, x, ponto)
        except Exception:
            return None
    receptor, emissor = contexto.Pipe(duplex=False)
    filho = contexto.Process(
        target=_trabalhador, args=(expr, ponto, direcao, emissor), daemon=True
    )
    filho.start()
    emissor.close()
    try:
        if not receptor.poll(tempo):
            return None
        tipo, valor = receptor.recv()
    except (EOFError, OSError):
        return None
    finally:
        if filho.is_alive():
            filho.kill()
        filho.join()
        receptor.close()
    return valor if tipo == "ok" else None
