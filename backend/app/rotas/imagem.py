"""Rota POST /limite/imagem: recebe a foto de uma conta de limite, usa o
Gemini para reconhecer a função e o ponto, e segue o mesmo caminho de
POST /limite a partir daí (ver `montar_resposta` em app.rotas.limite)."""
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.modelos.schemas import EntradaLimite, RespostaLimite
from app.motor.entrada import ErroEntrada, ler_funcao, ler_ponto
from app.rotas.limite import montar_resposta
from app.visao.gemini import (
    ErroConfiguracaoVisao, ErroExtracaoImagem, TIPOS_MIME_ACEITOS,
    extrair_funcao_e_ponto,
)

roteador = APIRouter()

TAMANHO_MAXIMO_BYTES = 5 * 1024 * 1024  # 5 MB


def _mensagem_de_reconhecimento(funcao_texto: str, ponto_texto: str, erro: ErroEntrada) -> str:
    """Deixa claro que o problema pode ser o reconhecimento da imagem (e não
    um erro da pessoa), mostrando o que foi lido."""
    motivo = str(erro)
    if motivo:
        motivo = motivo[0].lower() + motivo[1:]
    return (
        f"Reconhecemos «{funcao_texto}» (para x → {ponto_texto}), mas {motivo} "
        "Confira se a imagem está legível ou digite a função manualmente."
    )


@roteador.post("/limite/imagem", response_model=RespostaLimite)
async def calcular_limite_por_imagem(imagem: UploadFile = File(...)) -> RespostaLimite:
    tipo_mime = (imagem.content_type or "").lower()
    if tipo_mime not in TIPOS_MIME_ACEITOS:
        raise HTTPException(
            status_code=400,
            detail="Formato de imagem não aceito. Envie um arquivo PNG, JPEG ou WEBP.",
        )

    # Lê em pedaços e já corta se passar do limite, em vez de bufferizar um
    # upload enorme por completo só para descobrir depois que ele é grande
    # demais.
    dados = bytearray()
    while pedaco := await imagem.read(1024 * 1024):
        dados.extend(pedaco)
        if len(dados) > TAMANHO_MAXIMO_BYTES:
            raise HTTPException(
                status_code=400, detail="A imagem é grande demais (máximo de 5 MB)."
            )
    if not dados:
        raise HTTPException(status_code=400, detail="A imagem enviada está vazia.")
    dados = bytes(dados)

    try:
        funcao_texto, ponto_texto = extrair_funcao_e_ponto(dados, tipo_mime)
    except ErroConfiguracaoVisao as erro:
        raise HTTPException(status_code=500, detail=str(erro)) from erro
    except ErroExtracaoImagem as erro:
        raise HTTPException(status_code=400, detail=str(erro)) from erro

    entrada_echo = EntradaLimite(funcao=funcao_texto, ponto=ponto_texto)

    try:
        expressao = ler_funcao(funcao_texto)
        ponto = ler_ponto(ponto_texto)
    except ErroEntrada as erro:
        raise HTTPException(
            status_code=400,
            detail=_mensagem_de_reconhecimento(funcao_texto, ponto_texto, erro),
        ) from erro

    return montar_resposta(expressao, ponto, entrada_echo)
