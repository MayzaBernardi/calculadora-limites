// Comunicação com a API da Calculadora de Limites.
// Troque a porta/host aqui se o backend rodar em outro lugar.
const API_URL = "http://127.0.0.1:8000";

/**
 * Chama POST /limite. Em caso de sucesso devolve o corpo já em objeto
 * JavaScript (contrato RespostaLimite). Em caso de erro (da API ou de
 * rede) lança um Error cuja mensagem já está em português, pronta para
 * mostrar ao usuário.
 */
async function calcularLimite(funcao, ponto) {
  let resposta;
  try {
    resposta = await fetch(`${API_URL}/limite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ funcao, ponto }),
    });
  } catch (erroDeRede) {
    throw new Error("Não foi possível conectar ao servidor. Ele está rodando?");
  }

  let corpo;
  try {
    corpo = await resposta.json();
  } catch (erroDeParse) {
    throw new Error("O servidor respondeu em um formato inesperado.");
  }

  if (!resposta.ok) {
    const mensagem = corpo && typeof corpo.erro === "string"
      ? corpo.erro
      : "Ocorreu um erro ao calcular o limite.";
    throw new Error(mensagem);
  }

  return corpo;
}
