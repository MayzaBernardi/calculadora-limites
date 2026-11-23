// Renderização do gráfico da função, com o ponto do limite destacado,
// usando Chart.js. Não lê HTML/texto da API: `grafico.pontos`,
// `ponto_grafico` e `valor_grafico` já vêm como números (ou null).

// Guarda a instância atual do Chart.js para poder destruí-la antes de
// desenhar de novo (o usuário pode calcular outro limite na mesma página).
let instanciaGrafico = null;

/**
 * Lê as cores do tema atual (claro ou escuro) direto das variáveis CSS,
 * para o gráfico acompanhar o alternador de tema no momento em que é
 * desenhado. Não lê nenhum dado da API, só o estilo computado da página.
 */
function coresDoTema() {
  const estilo = getComputedStyle(document.documentElement);
  const ler = (nome, reserva) => estilo.getPropertyValue(nome).trim() || reserva;
  return {
    curva: ler("--cor-destaque", "#2e5aac"),
    marcador: ler("--cor-erro-borda", "#c0392b"),
    texto: ler("--cor-texto-suave", "#4a5063"),
    grade: ler("--cor-borda", "#d7d9e3"),
  };
}

/**
 * Recebe a resposta inteira da API e devolve um elemento <div> (com um
 * <canvas> dentro) já com o gráfico montado, pronto para ser anexado na
 * página. Não manipula o DOM global.
 */
function renderizarGrafico(resposta) {
  const container = document.createElement("div");
  container.className = "grafico-container aparecer";

  const canvas = document.createElement("canvas");
  canvas.setAttribute("role", "img");
  canvas.setAttribute(
    "aria-label",
    "Gráfico da função, com o ponto do limite destacado quando aplicável."
  );
  container.appendChild(canvas);

  const pontosCurva = resposta.grafico.pontos.map((ponto) => ({
    x: ponto.x,
    y: ponto.y,
  }));

  const cores = coresDoTema();

  const datasets = [
    {
      label: "f(x)",
      data: pontosCurva,
      borderColor: cores.curva,
      backgroundColor: cores.curva,
      borderWidth: 2.5,
      pointRadius: 0,
      spanGaps: false,
      tension: 0.05,
    },
  ];

  // Só desenha o marcador quando os dois vierem preenchidos: é a única
  // combinação em que há um ponto (x, y) de verdade para destacar.
  const temMarcador =
    resposta.ponto_grafico !== null &&
    resposta.ponto_grafico !== undefined &&
    resposta.valor_grafico !== null &&
    resposta.valor_grafico !== undefined;

  if (temMarcador) {
    datasets.push({
      label: "Limite",
      data: [{ x: resposta.ponto_grafico, y: resposta.valor_grafico }],
      showLine: false,
      pointRadius: 7,
      pointHoverRadius: 9,
      pointBorderWidth: 2,
      pointBorderColor: "#ffffff",
      backgroundColor: cores.marcador,
      borderColor: cores.marcador,
    });
  }

  if (instanciaGrafico) {
    instanciaGrafico.destroy();
  }

  instanciaGrafico = new Chart(canvas, {
    type: "line",
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 400, easing: "easeOutQuart" },
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          type: "linear",
          title: { display: true, text: "x", color: cores.texto },
          ticks: { color: cores.texto },
          grid: { color: cores.grade },
        },
        y: {
          type: "linear",
          title: { display: true, text: "f(x)", color: cores.texto },
          ticks: { color: cores.texto },
          grid: { color: cores.grade },
        },
      },
    },
  });

  return container;
}
