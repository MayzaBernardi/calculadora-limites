"""Integração com a API de visão do Gemini (Google): extrai a função e o
ponto de uma imagem de uma conta de limite escrita à mão ou impressa.

A chave (GEMINI_API_KEY) só é lida de variável de ambiente, e o cliente do
Gemini só é criado dentro de `extrair_funcao_e_ponto` (nunca no nível do
módulo), para o app e os testes continuarem funcionando sem a chave
configurada."""
import json
import os

from google import genai
from google.genai import types

MODELO = "gemini-3.6-flash"

# Timeout da chamada de rede ao Gemini (não precisa do multiprocessing que o
# motor usa para o sympy: é só uma chamada HTTP).
TEMPO_MAXIMO_SEGUNDOS = 25.0

TIPOS_MIME_ACEITOS = {"image/png", "image/jpeg", "image/jpg", "image/webp"}

# Mesma sintaxe que app.motor.entrada aceita (ler_funcao/ler_ponto): sen, tg,
# ln, raiz, piso, |u|, ^, e, pi, multiplicação implícita, infinito/-infinito.
PROMPT = """Você recebe uma foto (feita à mão ou impressa) de uma conta de \
limite de Cálculo: uma função de uma variável x e o valor para onde x tende.

Extraia duas informações e devolva como JSON:
- "funcao": a função de x, usando APENAS esta sintaxe:
  - operadores: + - * / ^ (potência) e parênteses
  - multiplicação implícita é permitida: 2x, 3x^2
  - funções disponíveis: sen, cos, tg, arcsen, arccos, arctg, ln, exp, raiz \
(raiz quadrada), piso (função piso/chão)
  - valor absoluto com barras: |x-1|
  - constantes: pi, e
  - a variável é sempre x (não use outra letra)
- "ponto": o valor para onde x tende: um número (inteiro, decimal ou \
fração como 1/2), ou a palavra "infinito", ou "-infinito".

Exemplos do formato esperado de saída:
1. Imagem mostra "lim(x->2) (x^2-4)/(x-2)"
   => {"funcao": "(x^2-4)/(x-2)", "ponto": "2"}
2. Imagem mostra "lim(x->0) sen(3x)/x"
   => {"funcao": "sen(3x)/x", "ponto": "0"}
3. Imagem mostra "lim(x->+inf) (1+1/x)^x"
   => {"funcao": "(1+1/x)^x", "ponto": "infinito"}
4. Imagem mostra "lim(x->-inf) 1/x"
   => {"funcao": "1/x", "ponto": "-infinito"}

Responda somente com os dois campos pedidos, sem explicações."""

ESQUEMA_RESPOSTA = {
    "type": "object",
    "properties": {
        "funcao": {"type": "string"},
        "ponto": {"type": "string"},
    },
    "required": ["funcao", "ponto"],
}


class ErroConfiguracaoVisao(Exception):
    """A chave do Gemini não está configurada no servidor."""


class ErroExtracaoImagem(Exception):
    """Falha ao extrair a função e o ponto de uma imagem: rede, timeout, ou
    resposta do Gemini fora do formato esperado. Mensagem em português,
    pronta para mostrar ao usuário."""


def _chave_configurada() -> str:
    chave = os.environ.get("GEMINI_API_KEY", "").strip()
    if not chave:
        raise ErroConfiguracaoVisao(
            "Recurso de entrada por imagem não está configurado no servidor."
        )
    return chave


def extrair_funcao_e_ponto(dados: bytes, tipo_mime: str) -> tuple[str, str]:
    """Envia a imagem ao Gemini e devolve (funcao, ponto) como texto simples,
    na sintaxe que app.motor.entrada.ler_funcao/ler_ponto já aceitam.

    Levanta ErroConfiguracaoVisao se a chave não estiver configurada, ou
    ErroExtracaoImagem se a chamada falhar (rede, timeout) ou a resposta não
    vier no formato esperado."""
    chave = _chave_configurada()

    try:
        cliente = genai.Client(api_key=chave)
        resposta = cliente.models.generate_content(
            model=MODELO,
            contents=[
                types.Part.from_bytes(data=dados, mime_type=tipo_mime),
                PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ESQUEMA_RESPOSTA,
                temperature=0,
                http_options=types.HttpOptions(
                    timeout=int(TEMPO_MAXIMO_SEGUNDOS * 1000)
                ),
            ),
        )
    except Exception as erro:
        raise ErroExtracaoImagem(
            "Não conseguimos processar a imagem agora (falha ao consultar o "
            "serviço de reconhecimento). Tente de novo em alguns instantes "
            "ou digite a função manualmente."
        ) from erro

    texto = (getattr(resposta, "text", None) or "").strip()
    if not texto:
        raise ErroExtracaoImagem(
            "Não conseguimos reconhecer uma conta de limite nessa imagem."
        )

    try:
        corpo = json.loads(texto)
    except json.JSONDecodeError as erro:
        raise ErroExtracaoImagem(
            "Não conseguimos reconhecer uma conta de limite nessa imagem."
        ) from erro

    if not isinstance(corpo, dict):
        raise ErroExtracaoImagem(
            "Não conseguimos reconhecer uma conta de limite nessa imagem."
        )

    funcao = corpo.get("funcao")
    ponto = corpo.get("ponto")
    if (
        not isinstance(funcao, str) or not funcao.strip()
        or not isinstance(ponto, str) or not ponto.strip()
    ):
        raise ErroExtracaoImagem(
            "Não conseguimos identificar a função e o ponto do limite nessa "
            "imagem."
        )

    return funcao.strip(), ponto.strip()
