"""Schemas Pydantic de entrada e saída da API. Este é o contrato que o
frontend consome: nomes de campo e significado não devem mudar sem avisar
quem consome a API."""
from pydantic import BaseModel, Field


class EntradaLimite(BaseModel):
    """Corpo de POST /limite."""

    funcao: str = Field(
        ..., description="A função de x. Ex.: (x^2-4)/(x-2), sen(3x)/x, (1+1/x)^x",
        examples=["(x^2-4)/(x-2)"],
    )
    ponto: str = Field(
        ..., description="Para onde x tende: um número, infinito ou -infinito",
        examples=["2"],
    )


class ValorResposta(BaseModel):
    """Um valor matemático (número, ∞, e, π...) em texto simples e em LaTeX."""

    texto: str
    latex: str


class PassoResposta(BaseModel):
    """Um passo da resolução, pronto para exibir: título, explicação em
    português e fórmula em LaTeX (sem $ nem \\( \\) em volta)."""

    titulo: str
    explicacao: str
    latex: str


class LateraisResposta(BaseModel):
    """Limites laterais (só faz sentido em ponto finito). Cada lado é None
    quando a função não está definida (nos reais) perto desse lado."""

    esquerda: ValorResposta | None
    direita: ValorResposta | None


class PontoGrafico(BaseModel):
    """Um ponto (x, y) do gráfico. y é None onde a função não está definida
    (assíntota, raiz de negativo etc.) — o frontend não deve ligar a linha
    entre os dois lados de um y=None."""

    x: float
    y: float | None


class GraficoResposta(BaseModel):
    pontos: list[PontoGrafico]


class RespostaLimite(BaseModel):
    """Resposta de sucesso de POST /limite.

    - `resolvido=False`: o motor não conseguiu concluir o limite (honesto,
      nunca um valor inventado). `existe` e `resultado` vêm None.
    - `resolvido=True, existe=False`: o limite não existe (ex.: laterais
      diferentes). `resultado` vem None.
    - `resolvido=True, existe=True`: `resultado` traz o valor.
    - `laterais` vem None quando o ponto é infinito (não faz sentido nesse
      caso); em ponto finito, vem um objeto com `esquerda`/`direita`, cada um
      podendo ser None se a função não existe nesse lado.
    - `ponto_grafico`: o x pedido, como float, para marcar no gráfico; None
      se o ponto pedido é infinito (não há x para desenhar).
    - `valor_grafico`: o y do resultado, como float, para marcar no gráfico;
      None se o limite não foi resolvido, não existe, ou o valor não é um
      número real finito (por exemplo, ∞).
    """

    entrada: EntradaLimite
    resolvido: bool
    existe: bool | None
    resultado: ValorResposta | None
    laterais: LateraisResposta | None
    passos: list[PassoResposta]
    grafico: GraficoResposta
    ponto_grafico: float | None
    valor_grafico: float | None


class RespostaErro(BaseModel):
    """Corpo de respostas de erro (400/422/500): sempre `{"erro": "..."}`,
    nunca stack trace."""

    erro: str
