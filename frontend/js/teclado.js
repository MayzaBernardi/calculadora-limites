// Teclado de símbolos: ajuda a montar a função e o ponto sem precisar
// digitar a sintaxe de cor (ver sintaxe aceita em backend/app/motor/entrada.py).
// Só manipula o texto/seleção dos dois campos já existentes (campo-funcao e
// campo-ponto); não altera o submit do formulário nem lê nada da API.
// Tudo dentro de uma IIFE para não poluir o escopo global compartilhado
// pelos outros scripts da página (evita colidir com nomes como
// `campoFuncao`/`campoPonto`, já usados em js/passos.js).
(function () {
  const botaoAlternar = document.getElementById("botao-alternar-teclado");
  const painelTeclado = document.getElementById("teclado-simbolos");
  const elCampoFuncao = document.getElementById("campo-funcao");
  const elCampoPonto = document.getElementById("campo-ponto");

  if (!botaoAlternar || !painelTeclado || !elCampoFuncao || !elCampoPonto) {
    return;
  }

  // Último campo de texto focado nesta visita à página; usa campo-funcao
  // como padrão enquanto nenhum dos dois recebeu foco ainda.
  let campoAtivo = elCampoFuncao;

  elCampoFuncao.addEventListener("focus", () => {
    campoAtivo = elCampoFuncao;
  });
  elCampoPonto.addEventListener("focus", () => {
    campoAtivo = elCampoPonto;
  });

  botaoAlternar.addEventListener("click", () => {
    const vaiAbrir = painelTeclado.hidden;
    painelTeclado.hidden = !vaiAbrir;
    botaoAlternar.setAttribute("aria-expanded", String(vaiAbrir));
    botaoAlternar.textContent = vaiAbrir
      ? "⌨ Ocultar teclado de símbolos"
      : "⌨ Mostrar teclado de símbolos";
  });

  /** Insere `texto` na posição do cursor, substituindo a seleção atual. */
  function inserirTexto(campo, texto) {
    const inicio = campo.selectionStart ?? campo.value.length;
    const fim = campo.selectionEnd ?? campo.value.length;
    const valor = campo.value;

    campo.value = valor.slice(0, inicio) + texto + valor.slice(fim);

    const posicaoFinal = inicio + texto.length;
    campo.focus();
    campo.setSelectionRange(posicaoFinal, posicaoFinal);
  }

  /**
   * Envolve a seleção atual com `prefixo`/`sufixo` (ex.: "sen(" / ")").
   * Sem seleção, insere a forma vazia com o cursor entre os dois, pronta
   * para a pessoa digitar o argumento.
   */
  function envolverSelecao(campo, prefixo, sufixo) {
    const inicio = campo.selectionStart ?? campo.value.length;
    const fim = campo.selectionEnd ?? campo.value.length;
    const valor = campo.value;
    const selecionado = valor.slice(inicio, fim);

    campo.value = valor.slice(0, inicio) + prefixo + selecionado + sufixo + valor.slice(fim);
    campo.focus();

    if (selecionado.length > 0) {
      const posicaoFinal = inicio + prefixo.length + selecionado.length + sufixo.length;
      campo.setSelectionRange(posicaoFinal, posicaoFinal);
    } else {
      const posicaoEntreParenteses = inicio + prefixo.length;
      campo.setSelectionRange(posicaoEntreParenteses, posicaoEntreParenteses);
    }
  }

  /** Apaga a seleção atual, ou 1 caractere antes do cursor (como Backspace). */
  function apagarCaractere(campo) {
    const inicio = campo.selectionStart ?? campo.value.length;
    const fim = campo.selectionEnd ?? campo.value.length;
    const valor = campo.value;
    campo.focus();

    if (inicio !== fim) {
      campo.value = valor.slice(0, inicio) + valor.slice(fim);
      campo.setSelectionRange(inicio, inicio);
    } else if (inicio > 0) {
      campo.value = valor.slice(0, inicio - 1) + valor.slice(inicio);
      campo.setSelectionRange(inicio - 1, inicio - 1);
    } else {
      campo.setSelectionRange(0, 0);
    }
  }

  /** Limpa o campo inteiro. */
  function limparCampo(campo) {
    campo.value = "";
    campo.focus();
    campo.setSelectionRange(0, 0);
  }

  // Um único listener no painel (delegação de evento) cobre todos os
  // botões do teclado, atuais e futuros, sem precisar de um listener por
  // botão. Nenhum deles é type="submit"; nunca disparam o formulário.
  painelTeclado.addEventListener("click", (evento) => {
    const botao = evento.target.closest("button");
    if (!botao || !painelTeclado.contains(botao)) {
      return;
    }

    const campo = campoAtivo;

    if (botao.dataset.prefixo !== undefined || botao.dataset.sufixo !== undefined) {
      envolverSelecao(campo, botao.dataset.prefixo || "", botao.dataset.sufixo || "");
    } else if (botao.dataset.inserir !== undefined) {
      inserirTexto(campo, botao.dataset.inserir);
    } else if (botao.dataset.acao === "apagar") {
      apagarCaractere(campo);
    } else if (botao.dataset.acao === "limpar") {
      limparCampo(campo);
    }
  });
})();
