"""Testes da API (POST /limite): contrato de entrada e saída, erros e CORS."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def _chamar(funcao: str, ponto: str) -> dict:
    resposta = cliente.post("/limite", json={"funcao": funcao, "ponto": ponto})
    return resposta


def test_substituicao_direta():
    resposta = _chamar("x^2 + 1", "3")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["resolvido"] is True
    assert corpo["existe"] is True
    assert corpo["resultado"] == {"texto": "10", "latex": "10"}
    assert corpo["laterais"] == {
        "esquerda": {"texto": "10", "latex": "10"},
        "direita": {"texto": "10", "latex": "10"},
    }
    assert len(corpo["passos"]) >= 1
    assert all({"titulo", "explicacao", "latex"} <= p.keys() for p in corpo["passos"])


def test_zero_sobre_zero_fatoracao():
    resposta = _chamar("(x^2-4)/(x-2)", "2")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["resolvido"] is True
    assert corpo["existe"] is True
    assert corpo["resultado"]["texto"] == "4"
    assert corpo["laterais"]["esquerda"]["texto"] == "4"
    assert corpo["laterais"]["direita"]["texto"] == "4"
    titulos = [p["titulo"] for p in corpo["passos"]]
    assert "Fatoração" in titulos
    assert any(r"\lim" in p["latex"] for p in corpo["passos"])


def test_limite_fundamental_zero_sobre_zero():
    resposta = _chamar("sen(x)/x", "0")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["resolvido"] is True
    assert corpo["existe"] is True
    assert corpo["resultado"]["texto"] == "1"


def test_limite_no_infinito():
    resposta = _chamar("(1+1/x)^x", "infinito")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["resolvido"] is True
    assert corpo["existe"] is True
    assert corpo["resultado"] == {"texto": "e", "latex": "e"}
    # x -> infinito: laterais não fazem sentido.
    assert corpo["laterais"] is None
    assert len(corpo["grafico"]["pontos"]) > 0


def test_limite_nao_existe_laterais_diferentes():
    resposta = _chamar("1/x", "0")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["resolvido"] is True
    assert corpo["existe"] is False
    assert corpo["resultado"] is None
    assert corpo["laterais"]["esquerda"]["texto"] == "-∞"
    assert corpo["laterais"]["direita"]["texto"] == "∞"


@pytest.mark.parametrize(
    "funcao,ponto",
    [
        ("", "0"),  # função vazia
        ("x+y", "0"),  # variável errada
        ("import os", "0"),  # símbolo não permitido
        ("x^2", ""),  # ponto vazio
    ],
)
def test_entrada_invalida_devolve_400(funcao, ponto):
    resposta = _chamar(funcao, ponto)
    assert resposta.status_code == 400
    corpo = resposta.json()
    assert "erro" in corpo
    assert isinstance(corpo["erro"], str) and corpo["erro"]
    # nunca deixa stack trace vazar
    assert "Traceback" not in corpo["erro"]


def test_corpo_de_requisicao_invalido_devolve_422_sem_stack_trace():
    resposta = cliente.post("/limite", json={"funcao": "x^2"})  # falta "ponto"
    assert resposta.status_code == 422
    corpo = resposta.json()
    assert "erro" in corpo
    assert "Traceback" not in corpo["erro"]


def test_resposta_tem_passos_latex_e_pontos_do_grafico():
    resposta = _chamar("(x^2-4)/(x-2)", "2")
    corpo = resposta.json()
    assert isinstance(corpo["passos"], list) and len(corpo["passos"]) > 0
    for passo in corpo["passos"]:
        assert isinstance(passo["titulo"], str) and passo["titulo"]
        assert isinstance(passo["explicacao"], str) and passo["explicacao"]
        assert isinstance(passo["latex"], str) and passo["latex"]

    pontos = corpo["grafico"]["pontos"]
    assert isinstance(pontos, list) and len(pontos) > 1
    for ponto in pontos:
        assert set(ponto.keys()) == {"x", "y"}
        assert isinstance(ponto["x"], float)
        assert ponto["y"] is None or isinstance(ponto["y"], float)
    # o ponto x=2 (fora do domínio) deve aparecer com y=None, sem "ligar"
    # os dois lados da assíntota/furo no gráfico.
    assert any(ponto["y"] is None for ponto in pontos)


def test_grafico_marca_descontinuidade_com_none():
    resposta = _chamar("1/x", "0")
    pontos = resposta.json()["grafico"]["pontos"]
    valores_x = [p["x"] for p in pontos]
    # x=0 deve estar na malha (janela ponto±5, número de pontos ímpar) e vir None.
    assert 0.0 in valores_x
    indice = valores_x.index(0.0)
    assert pontos[indice]["y"] is None


def test_timeout_devolve_400_sem_500(monkeypatch):
    """Simula o cálculo estourando o tempo (sem precisar de uma função que
    realmente demore 10s de verdade): devolve 400 com mensagem clara, nunca
    um 500 ou stack trace."""
    import app.rotas.limite as modulo_limite

    monkeypatch.setattr(modulo_limite, "_resolver_com_timeout", lambda *a, **k: (False, None))
    resposta = _chamar("x^2", "1")
    assert resposta.status_code == 400
    corpo = resposta.json()
    assert "erro" in corpo and "tempo" in corpo["erro"].lower()


def test_ponto_e_valor_grafico_substituicao_direta():
    resposta = _chamar("(x^2-4)/(x-2)", "2")
    corpo = resposta.json()
    assert corpo["ponto_grafico"] == 2.0
    assert corpo["valor_grafico"] == 4.0


def test_ponto_e_valor_grafico_limite_nao_existe():
    resposta = _chamar("1/x", "0")
    corpo = resposta.json()
    assert corpo["ponto_grafico"] == 0.0
    assert corpo["valor_grafico"] is None


def test_ponto_e_valor_grafico_ponto_infinito():
    resposta = _chamar("(1+1/x)^x", "infinito")
    corpo = resposta.json()
    assert corpo["ponto_grafico"] is None
    assert corpo["valor_grafico"] == pytest.approx(2.718281828, rel=1e-6)


def test_ponto_e_valor_grafico_so_um_lado_definido():
    resposta = _chamar("ln(x)", "0")
    corpo = resposta.json()
    assert corpo["ponto_grafico"] == 0.0
    assert corpo["valor_grafico"] is None


def test_ponto_e_valor_grafico_nao_resolvido():
    resposta = _chamar("sen(1/x)", "0")
    corpo = resposta.json()
    assert corpo["resolvido"] is False
    assert corpo["ponto_grafico"] == 0.0
    assert corpo["valor_grafico"] is None


def test_ponto_e_valor_grafico_resultado_fracionario():
    resposta = _chamar("(x^3-1)/(x-1)", "1")
    corpo = resposta.json()
    assert corpo["ponto_grafico"] == 1.0
    assert corpo["valor_grafico"] == 3.0


def test_cors_header_presente():
    resposta = cliente.post(
        "/limite",
        json={"funcao": "x^2", "ponto": "1"},
        headers={"Origin": "http://localhost:5500"},
    )
    assert resposta.status_code == 200
    assert resposta.headers.get("access-control-allow-origin") == "http://localhost:5500"


# --- POST /limite/imagem ---------------------------------------------------
#
# A suíte automatizada nunca chama o Gemini de verdade: `extrair_funcao_e_ponto`
# é sempre substituída por monkeypatch, tanto para não depender de rede/chave
# quanto para não gastar cota da API em CI.

_PNG_MINIMO = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\xdac\xf8\xcf\xc0\x00"
    b"\x00\x00\x03\x00\x01\x1a\x0b\x92\xf5\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _enviar_imagem(conteudo: bytes = _PNG_MINIMO, tipo: str = "image/png", nome: str = "conta.png"):
    return cliente.post("/limite/imagem", files={"imagem": (nome, conteudo, tipo)})


def test_imagem_valida_segue_mesmo_contrato_de_limite(monkeypatch):
    import app.rotas.imagem as modulo_imagem

    monkeypatch.setattr(
        modulo_imagem, "extrair_funcao_e_ponto",
        lambda dados, tipo_mime: ("(x^2-4)/(x-2)", "2"),
    )
    resposta = _enviar_imagem()
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["entrada"] == {"funcao": "(x^2-4)/(x-2)", "ponto": "2"}
    assert corpo["resolvido"] is True
    assert corpo["existe"] is True
    assert corpo["resultado"]["texto"] == "4"
    assert len(corpo["passos"]) >= 1
    assert len(corpo["grafico"]["pontos"]) > 1


def test_imagem_tipo_de_arquivo_invalido_devolve_400(monkeypatch):
    import app.rotas.imagem as modulo_imagem

    chamou = False

    def _nao_deveria_chamar(dados, tipo_mime):
        nonlocal chamou
        chamou = True
        return ("x", "0")

    monkeypatch.setattr(modulo_imagem, "extrair_funcao_e_ponto", _nao_deveria_chamar)
    resposta = _enviar_imagem(tipo="application/pdf", nome="conta.pdf")
    assert resposta.status_code == 400
    corpo = resposta.json()
    assert "erro" in corpo and corpo["erro"]
    assert "Traceback" not in corpo["erro"]
    assert not chamou  # nem chega a gastar uma chamada ao Gemini


def test_imagem_grande_demais_devolve_400(monkeypatch):
    import app.rotas.imagem as modulo_imagem

    chamou = False

    def _nao_deveria_chamar(dados, tipo_mime):
        nonlocal chamou
        chamou = True
        return ("x", "0")

    monkeypatch.setattr(modulo_imagem, "extrair_funcao_e_ponto", _nao_deveria_chamar)
    conteudo_grande = b"\x00" * (5 * 1024 * 1024 + 1)
    resposta = _enviar_imagem(conteudo=conteudo_grande)
    assert resposta.status_code == 400
    corpo = resposta.json()
    assert "erro" in corpo and corpo["erro"]
    assert not chamou


def test_imagem_erro_de_extracao_devolve_400(monkeypatch):
    import app.rotas.imagem as modulo_imagem
    from app.visao.gemini import ErroExtracaoImagem

    def _levanta(dados, tipo_mime):
        raise ErroExtracaoImagem("Não conseguimos reconhecer uma conta de limite nessa imagem.")

    monkeypatch.setattr(modulo_imagem, "extrair_funcao_e_ponto", _levanta)
    resposta = _enviar_imagem()
    assert resposta.status_code == 400
    corpo = resposta.json()
    assert "erro" in corpo
    assert "reconhec" in corpo["erro"].lower()
    assert "Traceback" not in corpo["erro"]


def test_imagem_texto_reconhecido_invalido_devolve_400_com_contexto(monkeypatch):
    """Função reconhecida usa um caractere fora do whitelist de entrada.py:
    o erro deve citar o que foi reconhecido, para a pessoa entender que pode
    ter sido um problema de leitura da imagem."""
    import app.rotas.imagem as modulo_imagem

    monkeypatch.setattr(
        modulo_imagem, "extrair_funcao_e_ponto",
        lambda dados, tipo_mime: ("x + y", "0"),
    )
    resposta = _enviar_imagem()
    assert resposta.status_code == 400
    corpo = resposta.json()
    assert "erro" in corpo
    assert "x + y" in corpo["erro"]
    assert "Traceback" not in corpo["erro"]


def test_imagem_sem_chave_configurada_devolve_500_sem_derrubar_processo(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    resposta = _enviar_imagem()
    assert resposta.status_code == 500
    corpo = resposta.json()
    assert "erro" in corpo and corpo["erro"]
    assert "Traceback" not in corpo["erro"]
    # o processo continua no ar: a rota de texto segue funcionando.
    resposta_texto = _chamar("x^2", "1")
    assert resposta_texto.status_code == 200

