// Renderização do gráfico da função, com o ponto do limite destacado,
// usando Chart.js. Não lê HTML/texto da API: `grafico.pontos`,
// `ponto_grafico` e `valor_grafico` já vêm como números (ou null).

// Guarda a instância atual do Chart.js para poder destruí-la antes de
// desenhar de novo (o usuário pode calcular outro limite na mesma página).
let instanciaGrafico = null;

/**
 * Recebe a resposta inteira da API e devolve um elemento <div> (com um
 * <canvas> dentro) já com o gráfico montado, pronto para ser anexado na
 * página. Não manipula o DOM global.
 */
function renderizarGrafico(resposta) {
  const container = document.createElement("div");
  container.className = "grafico-container";

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

  const datasets = [
    {
      label: "f(x)",
      data: pontosCurva,
      borderColor: "#2e5aac",
      backgroundColor: "#2e5aac",
      borderWidth: 2,
      pointRadius: 0,
      spanGaps: false,
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
      pointRadius: 6,
      pointHoverRadius: 7,
      backgroundColor: "#c0392b",
      borderColor: "#c0392b",
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
      animation: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          type: "linear",
          title: { display: true, text: "x" },
        },
        y: {
          type: "linear",
          title: { display: true, text: "f(x)" },
        },
      },
    },
  });

  return container;
}
