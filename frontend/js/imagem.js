// Entrada por imagem (Etapa 10): escolher um arquivo ou colar com Ctrl+V uma
// foto de uma conta de limite feita no papel, pré-visualizar e calcular via
// POST /limite/imagem. Reaproveita `calcularLimitePorImagem` (js/api.js) e
// `exibirResposta`/`limparErro`/`mostrarErro`/`limparResultado` (js/passos.js)
// — nenhuma lógica de renderização do resultado é duplicada aqui. Nenhum
// dado da API entra via innerHTML; só textContent (o KaTeX continua sendo
// acionado só dentro de js/passos.js).

const TIPOS_ACEITOS_IMAGEM = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
const TAMANHO_MAXIMO_IMAGEM_BYTES = 5 * 1024 * 1024; // 5 MB, mesmo limite da API

const areaImagem = document.getElementById("area-imagem");
const campoImagem = document.getElementById("campo-imagem");
const previaImagem = document.getElementById("previa-imagem");
const previaImagemImg = document.getElementById("previa-imagem-img");
const botaoRemoverImagem = document.getElementById("botao-remover-imagem");
const botaoCalcularImagem = document.getElementById("botao-calcular-imagem");

// Arquivo atualmente escolhido/colado e a URL de pré-visualização (precisa
// ser revogada ao trocar de imagem, para não acumular memória).
let arquivoImagemAtual = null;
let urlPreviaImagemAtual = null;

/**
 * Validação só de ajuda no cliente (tipo e tamanho); a validação que vale
 * de verdade é sempre a da API. Devolve uma mensagem em português se o
 * arquivo não serve, ou null se está tudo certo.
 */
function validarArquivoImagem(arquivo) {
  if (!arquivo) {
    return "Nenhuma imagem selecionada.";
  }
  if (!TIPOS_ACEITOS_IMAGEM.includes(arquivo.type)) {
    return "Formato de imagem não aceito. Envie um arquivo PNG, JPEG ou WEBP.";
  }
  if (arquivo.size > TAMANHO_MAXIMO_IMAGEM_BYTES) {
    return "A imagem é grande demais (máximo de 5 MB).";
  }
  return null;
}

function definirImagemSelecionada(arquivo) {
  limparErro();

  const mensagemInvalida = validarArquivoImagem(arquivo);
  if (mensagemInvalida) {
    mostrarErro(mensagemInvalida);
    campoImagem.value = "";
    return;
  }

  arquivoImagemAtual = arquivo;

  if (urlPreviaImagemAtual) {
    URL.revokeObjectURL(urlPreviaImagemAtual);
  }
  urlPreviaImagemAtual = URL.createObjectURL(arquivo);
  previaImagemImg.src = urlPreviaImagemAtual;

  previaImagem.hidden = false;
  botaoCalcularImagem.disabled = false;
}

function removerImagemSelecionada() {
  arquivoImagemAtual = null;

  if (urlPreviaImagemAtual) {
    URL.revokeObjectURL(urlPreviaImagemAtual);
    urlPreviaImagemAtual = null;
  }
  previaImagemImg.removeAttribute("src");
  previaImagem.hidden = true;
  campoImagem.value = "";
  botaoCalcularImagem.disabled = true;
}

function definirCarregandoImagem(carregando) {
  botaoCalcularImagem.disabled = carregando || !arquivoImagemAtual;
  botaoRemoverImagem.disabled = carregando;
  // Impede disparar os dois cálculos (texto e imagem) ao mesmo tempo.
  botaoCalcular.disabled = carregando;
  indicadorCarregando.hidden = !carregando;
}

campoImagem.addEventListener("change", () => {
  const arquivo = campoImagem.files && campoImagem.files[0];
  if (arquivo) {
    definirImagemSelecionada(arquivo);
  }
});

botaoRemoverImagem.addEventListener("click", () => {
  removerImagemSelecionada();
});

botaoCalcularImagem.addEventListener("click", async () => {
  if (!arquivoImagemAtual) {
    mostrarErro("Escolha ou cole uma imagem antes de calcular.");
    return;
  }

  const mensagemInvalida = validarArquivoImagem(arquivoImagemAtual);
  if (mensagemInvalida) {
    mostrarErro(mensagemInvalida);
    return;
  }

  limparErro();
  limparResultado();
  definirCarregandoImagem(true);

  try {
    const resposta = await calcularLimitePorImagem(arquivoImagemAtual);
    exibirResposta(resposta, { mostrarReconhecimento: true });
  } catch (erro) {
    mostrarErro(erro.message);
  } finally {
    definirCarregandoImagem(false);
  }
});

// Colar com Ctrl+V: o jeito explicitamente pedido para enviar a imagem. O
// listener fica no document porque o evento de colar é disparado no
// elemento focado no momento (um campo de texto, ou o body); anexar aqui
// cobre a página inteira, sem depender de onde está o foco.
document.addEventListener("paste", (evento) => {
  const itens = evento.clipboardData && evento.clipboardData.items;
  if (!itens) {
    return;
  }

  for (const item of itens) {
    if (item.kind === "file" && item.type.startsWith("image/")) {
      const arquivo = item.getAsFile();
      if (arquivo) {
        evento.preventDefault();
        definirImagemSelecionada(arquivo);
      }
      break;
    }
  }
});

// Arrastar e soltar (extra, não obrigatório): o input de arquivo nativo já
// cobre teclado/leitor de tela sozinho; isto só acrescenta uma forma a mais.
areaImagem.addEventListener("dragover", (evento) => {
  evento.preventDefault();
  areaImagem.classList.add("area-imagem-arrastando");
});

areaImagem.addEventListener("dragleave", () => {
  areaImagem.classList.remove("area-imagem-arrastando");
});

areaImagem.addEventListener("drop", (evento) => {
  evento.preventDefault();
  areaImagem.classList.remove("area-imagem-arrastando");
  const arquivo = evento.dataTransfer && evento.dataTransfer.files && evento.dataTransfer.files[0];
  if (arquivo) {
    definirImagemSelecionada(arquivo);
  }
});
