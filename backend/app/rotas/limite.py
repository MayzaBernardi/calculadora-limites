"""Rota POST /limite: calcula o limite e monta a resposta para o frontend."""
import multiprocessing
import re

import sympy as sp
from fastapi import APIRouter, HTTPException

from app.grafico.pontos import calcular_pontos
from app.modelos.schemas import (
    EntradaLimite, GraficoResposta, LateraisResposta, PassoResposta,
    PontoGrafico, RespostaLimite, ValorResposta,
)
from app.motor.entrada import ErroEntrada, ler_funcao, ler_ponto
from app.motor.passos import tex, texto_ponto
from app.motor.resolvedor import resolver

roteador = APIRouter()

# Teto para a chamada completa a resolver(): a recursão entre técnicas
# encadeia vários sp.limit (cada um já protegido por 3s em limite_seguro),
# então o tempo total pode passar disso para uma entrada patológica.
TEMPO_MAXIMO_RESOLUCAO = 10.0


def _trabalhador(funcao, args, conexao) -> None:
    try:
        conexao.send(("ok", funcao(*args)))
    except BaseException as erro:  # noqa: BLE001 - qualquer falha vira (False, None)
        conexao.send(("erro", repr(erro)))
    finally:
        conexao.close()


def _resolver_com_timeout(expressao: sp.Expr, ponto: sp.Expr, tempo: float):
    """Como app.motor.seguro.executar_com_timeout, mas com processo NÃO
    daemon: resolver() já roda sp.limit em processos filhos (via
    limite_seguro), e um processo daemon não pode ter filhos (o
    multiprocessing levanta AssertionError nesse caso). Devolve (True,
    Resultado) ou (False, None) se passar do tempo ou falhar."""
    try:
        contexto = multiprocessing.get_context("fork")
    except ValueError:
        try:
            return True, resolver(expressao, ponto)
        except Exception:
            return False, None
    receptor, emissor = contexto.Pipe(duplex=False)
    filho = contexto.Process(
        target=_trabalhador, args=(resolver, (expressao, ponto), emissor), daemon=False
    )
    filho.start()
    emissor.close()
    try:
        if not receptor.poll(tempo):
            return False, None
        tipo, valor = receptor.recv()
    except (EOFError, OSError):
        return False, None
    finally:
        if filho.is_alive():
            filho.kill()
        filho.join()
        receptor.close()
    return (True, valor) if tipo == "ok" else (False, None)


_CONSTANTE_E = re.compile(r"\bE\b")


def _texto_valor(valor: sp.Expr) -> str:
    """texto_ponto, mas com a constante de Euler em minúscula (E -> e), como
    é escrita fora do SymPy."""
    return _CONSTANTE_E.sub("e", texto_ponto(valor))


def _valor_resposta(valor: sp.Expr) -> ValorResposta:
    return ValorResposta(texto=_texto_valor(valor), latex=tex(valor))


def montar_resposta(
    expressao: sp.Expr, ponto: sp.Expr, entrada_echo: EntradaLimite
) -> RespostaLimite:
    """Resolve o limite (com timeout) e monta a RespostaLimite a partir do
    Resultado do motor. Compartilhada entre POST /limite (função/ponto
    digitados) e POST /limite/imagem (função/ponto reconhecidos na foto):
    uma vez com a expressão e o ponto já lidos (sp.Expr), o resto do
    caminho é idêntico. `entrada_echo` só preenche o campo `entrada` da
    resposta (o que foi digitado, ou o que foi reconhecido na imagem)."""
    ok, resultado = _resolver_com_timeout(expressao, ponto, TEMPO_MAXIMO_RESOLUCAO)
    if not ok:
        raise HTTPException(
            status_code=400,
            detail=(
                "Não conseguimos calcular esse limite a tempo. "
                "Tente uma função mais simples."
            ),
        )

    resultado_resp = None
    if resultado.existe and resultado.valor is not None:
        resultado_resp = _valor_resposta(resultado.valor)

    laterais_resp = None
    if ponto.is_finite:
        laterais_resp = LateraisResposta(
            esquerda=(
                _valor_resposta(resultado.esquerda)
                if resultado.esquerda is not None else None
            ),
            direita=(
                _valor_resposta(resultado.direita)
                if resultado.direita is not None else None
            ),
        )

    passos_resp = [
        PassoResposta(titulo=p.titulo, explicacao=p.explicacao, latex=p.latex)
        for p in resultado.passos
    ]

    grafico_resp = GraficoResposta(
        pontos=[PontoGrafico(x=px, y=py) for px, py in calcular_pontos(expressao, ponto)]
    )

    ponto_grafico = float(ponto) if ponto.is_finite else None

    valor_grafico = None
    if (
        resultado.resolvido and resultado.existe and resultado.valor is not None
        and resultado.valor.is_finite and resultado.valor.is_real
    ):
        try:
            valor_grafico = float(resultado.valor)
        except (TypeError, ValueError):
            valor_grafico = None

    return RespostaLimite(
        entrada=entrada_echo,
        resolvido=resultado.resolvido,
        existe=resultado.existe,
        resultado=resultado_resp,
        laterais=laterais_resp,
        passos=passos_resp,
        grafico=grafico_resp,
        ponto_grafico=ponto_grafico,
        valor_grafico=valor_grafico,
    )


@roteador.post("/limite", response_model=RespostaLimite)
def calcular_limite(entrada: EntradaLimite) -> RespostaLimite:
    try:
        expressao = ler_funcao(entrada.funcao)
        ponto = ler_ponto(entrada.ponto)
    except ErroEntrada as erro:
        raise HTTPException(status_code=400, detail=str(erro)) from erro

    return montar_resposta(expressao, ponto, entrada)
