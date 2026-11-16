"""Ponto de entrada da API: instancia o FastAPI, configura CORS e inclui as
rotas. Nunca deixa stack trace vazar: todo erro vira {"erro": "..."}."""
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.rotas.limite import roteador

app = FastAPI(title="Calculadora de Limites com Passo a Passo")

# Origens liberadas para o frontend local, configuráveis por variável de
# ambiente (ORIGENS_PERMITIDAS, separadas por vírgula) para não precisar
# editar código ao trocar de porta/host. Sem allow_credentials: o projeto
# não usa cookies nem autenticação, e allow_credentials=True junto de várias
# origens (ou de "*") seria inseguro.
ORIGENS_PADRAO = [
    "http://localhost:5500", "http://127.0.0.1:5500",
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:8080", "http://127.0.0.1:8080",
    "http://localhost:3000", "http://127.0.0.1:3000",
]
_origens_env = os.environ.get("ORIGENS_PERMITIDAS", "")
ORIGENS_PERMITIDAS = (
    [o.strip() for o in _origens_env.split(",") if o.strip()]
    if _origens_env.strip() else ORIGENS_PADRAO
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_PERMITIDAS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(roteador)


@app.exception_handler(HTTPException)
def tratar_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Mesmo formato de erro ({"erro": "..."}) para 400, 404 etc."""
    detalhe = exc.detail if isinstance(exc.detail, str) else "Erro na requisição."
    return JSONResponse(status_code=exc.status_code, content={"erro": detalhe})


@app.exception_handler(RequestValidationError)
def tratar_erro_de_validacao(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Corpo da requisição mal formado (campo faltando, tipo errado etc.)."""
    return JSONResponse(
        status_code=422,
        content={"erro": "Dados de entrada inválidos: confira os campos «funcao» e «ponto»."},
    )


@app.exception_handler(Exception)
def tratar_erro_inesperado(request: Request, exc: Exception) -> JSONResponse:
    """Último recurso: nunca expõe o stack trace ao usuário."""
    return JSONResponse(
        status_code=500,
        content={"erro": "Erro interno ao calcular o limite. Tente novamente."},
    )
