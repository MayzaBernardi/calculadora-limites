// Renderização do resultado e dos passos na página. Todo texto que vem da
// API é colocado com textContent (nunca innerHTML); só o KaTeX escreve
// marcação, e só a partir do campo `latex` de cada item.

const formulario = document.getElementById("form-limite");
const campoFuncao = document.getElementById("campo-funcao");
const campoPonto = document.getElementById("campo-ponto");
const botaoCalcular = document.getElementById("botao-calcular");
const indicadorCarregando = document.getElementById("indicador-carregando");
const areaErro = document.getElementById("area-erro");
const areaResultado = document.getElementById("area-resultado");

function limparErro() {
  areaErro.hidden = true;
  areaErro.textContent = "";
}

function mostrarErro(mensagem) {
  areaErro.textContent = mensagem;
  areaErro.hidden = false;
}

function limparResultado() {
  areaResultado.innerHTML = "";
}

function renderizarFormula(latex, elemento) {
  if (typeof katex !== "undefined") {
    katex.render(latex, elemento, { throwOnError: false });
  } else {
    // Sem KaTeX carregado (ex.: falha de rede no CDN): mostra o LaTeX puro.
    elemento.textContent = latex;
  }
}

function criarBlocoLateral(titulo, valor) {
  const div = document.createElement("div");
  div.className = "lateral";

  const h3 = document.createElement("h3");
  h3.textContent = titulo;
  div.appendChild(h3);

  const formula = document.createElement("div");
  if (valor) {
    renderizarFormula(valor.latex, formula);
  } else {
    formula.textContent = "Não definido nesse lado.";
  }
  div.appendChild(formula);

  return div;
}

function renderizarResultado(resposta) {
  const bloco = document.createElement("div");
  bloco.className = "bloco-resultado aparecer";

  const h2 = document.createElement("h2");

  if (!resposta.resolvido) {
    bloco.classList.add("nao-resolvido");
    h2.textContent = "Não conseguimos concluir este limite";
    bloco.appendChild(h2);
  } else if (!resposta.existe) {
    bloco.classList.add("nao-existe");
    h2.textContent = "O limite não existe";
    bloco.appendChild(h2);
  } else {
    h2.textContent = "Resultado";
    bloco.appendChild(h2);

    const formula = document.createElement("div");
    formula.className = "formula-resultado";
    renderizarFormula(resposta.resultado.latex, formula);
    bloco.appendChild(formula);
  }

  if (resposta.laterais) {
    const divLaterais = document.createElement("div");
    divLaterais.className = "laterais";
    divLaterais.appendChild(criarBlocoLateral("Limite pela esquerda", resposta.laterais.esquerda));
    divLaterais.appendChild(criarBlocoLateral("Limite pela direita", resposta.laterais.direita));
    bloco.appendChild(divLaterais);
  }

  return bloco;
}

function renderizarPassos(passos) {
  const secao = document.createElement("div");
  secao.className = "aparecer";

  const titulo = document.createElement("h2");
  titulo.className = "titulo-secao-passos";
  titulo.textContent = "Passo a passo";
  secao.appendChild(titulo);

  const lista = document.createElement("ol");
  lista.className = "lista-passos";

  passos.forEach((passo, indice) => {
    const item = document.createElement("li");
    item.className = "passo";
    // Atraso crescente só para o efeito visual de entrada escalonada;
    // nenhum dado da API entra aqui, é só a posição do passo na lista.
    item.style.setProperty("--indice", indice);

    const tituloPasso = document.createElement("div");
    tituloPasso.className = "passo-titulo";
    tituloPasso.textContent = passo.titulo;
    item.appendChild(tituloPasso);

    const explicacaoPasso = document.createElement("div");
    explicacaoPasso.className = "passo-explicacao";
    explicacaoPasso.textContent = passo.explicacao;
    item.appendChild(explicacaoPasso);

    const formulaPasso = document.createElement("div");
    formulaPasso.className = "passo-formula";
    renderizarFormula(passo.latex, formulaPasso);
    item.appendChild(formulaPasso);

    lista.appendChild(item);
  });

  secao.appendChild(lista);
  return secao;
}

/**
 * Monta o aviso "Reconhecemos: f(x) = ..., x → ..." exibido quando o
 * resultado vem da entrada por imagem. `entrada` é o eco que a API devolve
 * (o que o Gemini leu na foto); todo o texto dinâmico entra via
 * textContent, nunca innerHTML.
 */
function criarBlocoReconhecimento(entrada) {
  const div = document.createElement("div");
  div.className = "bloco-reconhecimento aparecer";

  const paragrafo = document.createElement("p");

  const rotulo = document.createElement("strong");
  rotulo.textContent = "Reconhecemos na imagem: ";
  paragrafo.appendChild(rotulo);

  const trechoFuncao = document.createElement("span");
  trechoFuncao.className = "reconhecimento-valor";
  trechoFuncao.textContent = "f(x) = " + entrada.funcao;
  paragrafo.appendChild(trechoFuncao);

  paragrafo.appendChild(document.createTextNode(", x → "));

  const trechoPonto = document.createElement("span");
  trechoPonto.className = "reconhecimento-valor";
  trechoPonto.textContent = entrada.ponto;
  paragrafo.appendChild(trechoPonto);

  div.appendChild(paragrafo);

  const dica = document.createElement("p");
  dica.className = "reconhecimento-dica";
  dica.textContent =
    "Confira se a leitura está correta. Se não estiver, digite a função manualmente acima.";
  div.appendChild(dica);

  return div;
}

function exibirResposta(resposta, opcoes = {}) {
  limparResultado();
  if (opcoes.mostrarReconhecimento) {
    areaResultado.appendChild(criarBlocoReconhecimento(resposta.entrada));
  }
  areaResultado.appendChild(renderizarResultado(resposta));
  if (resposta.grafico && resposta.grafico.pontos && resposta.grafico.pontos.length > 0) {
    areaResultado.appendChild(renderizarGrafico(resposta));
  }
  if (resposta.passos && resposta.passos.length > 0) {
    areaResultado.appendChild(renderizarPassos(resposta.passos));
  }
}

function definirCarregando(carregando) {
  botaoCalcular.disabled = carregando;
  // Impede disparar os dois cálculos (texto e imagem) ao mesmo tempo;
  // botaoCalcularImagem só existe se js/imagem.js (Etapa 10) estiver carregado.
  if (typeof botaoCalcularImagem !== "undefined") {
    botaoCalcularImagem.disabled = carregando || !arquivoImagemAtual;
  }
  indicadorCarregando.hidden = !carregando;
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();

  const funcao = campoFuncao.value.trim();
  const ponto = campoPonto.value.trim();

  limparErro();
  limparResultado();
  definirCarregando(true);

  try {
    const resposta = await calcularLimite(funcao, ponto);
    exibirResposta(resposta);
  } catch (erro) {
    mostrarErro(erro.message);
  } finally {
    definirCarregando(false);
  }
});
