// Teclas da calculadora: ajudam a montar a função e o ponto sem precisar
// digitar a sintaxe de cor (ver sintaxe aceita em backend/app/motor/entrada.py).
// Só manipulam o texto/seleção dos dois campos já existentes (campo-funcao e
// campo-ponto); não alteram o envio do formulário nem leem nada da API. O
// botão "=" é o próprio #botao-calcular (type="submit", ver index.html) e não
// é selecionado por `inicializar` (não tem nenhum data-inserir/data-prefixo/
// data-sufixo/data-acao), então o envio nativo do form continua funcionando
// normal, tanto pelo clique nele quanto pelo Enter num dos dois campos.
// Tudo dentro de uma IIFE para não poluir o escopo global compartilhado
// pelos outros scripts da página (evita colidir com nomes como
// `campoFuncao`/`campoPonto`, já usados em js/passos.js).
(function () {
  function inicializar() {
    const elCampoFuncao = document.getElementById("campo-funcao");
    const elCampoPonto = document.getElementById("campo-ponto");
    // Só as teclas de verdade (exclui o "=", que não tem nenhum destes
    // atributos): um listener por botão, em vez de delegação a partir do
    // form, para o clique não depender de nada bolhar por um ancestral.
    const teclas = document.querySelectorAll(
      "[data-inserir], [data-prefixo], [data-sufixo], [data-acao]"
    );

    if (!elCampoFuncao || !elCampoPonto || teclas.length === 0) {
      console.error(
        "Teclado da calculadora: não encontrei os campos ou as teclas no HTML; os botões não vão funcionar."
      );
      return;
    }

    const CLASSE_LINHA_ATIVA = "calculadora-linha-display--ativa";

    /**
     * Mostra, de forma visível e permanente (não só o anel de foco do
     * navegador, que some assim que o foco sai do campo), qual dos dois
     * campos vai receber a próxima tecla clicada. Sem isso, dar Tab ou
     * clicar em "x tende a" e depois clicar numa tecla pensando em
     * "Função f(x)" insere o caractere no campo errado, sem nenhum aviso
     * visual — foi exatamente esse bug que a dona do projeto relatou.
     */
    function marcarCampoAtivo(campo) {
      const linhaFuncao = elCampoFuncao.closest(".calculadora-linha-display");
      const linhaPonto = elCampoPonto.closest(".calculadora-linha-display");
      if (linhaFuncao) {
        linhaFuncao.classList.toggle(CLASSE_LINHA_ATIVA, campo === elCampoFuncao);
      }
      if (linhaPonto) {
        linhaPonto.classList.toggle(CLASSE_LINHA_ATIVA, campo === elCampoPonto);
      }
    }

    // Último campo de texto focado nesta visita à página; usa campo-funcao
    // como padrão enquanto nenhum dos dois recebeu foco ainda.
    let campoAtivo = elCampoFuncao;
    marcarCampoAtivo(campoAtivo);

    elCampoFuncao.addEventListener("focus", () => {
      campoAtivo = elCampoFuncao;
      marcarCampoAtivo(campoAtivo);
    });
    elCampoPonto.addEventListener("focus", () => {
      campoAtivo = elCampoPonto;
      marcarCampoAtivo(campoAtivo);
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
     * Envolve a seleção atual com `prefixo`/`sufixo` (ex.: "raiz(" / ")").
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

    // Um listener por tecla (em vez de delegação a partir do form): cada
    // clique (ou Enter/Espaço com a tecla focada) dispara direto no botão
    // clicado, sem depender do evento bolhar por nenhum ancestral.
    teclas.forEach((botao) => {
      botao.addEventListener("click", () => {
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
    });
  }

  // Script carregado no fim do <body>, então o DOM já deveria estar pronto;
  // o `if` é só uma proteção extra, caso algo atrase a execução a ponto do
  // documento ainda estar carregando.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar);
  } else {
    inicializar();
  }
})();
