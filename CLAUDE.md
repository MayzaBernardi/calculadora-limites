# Calculadora de Limites com Passo a Passo

@CONTEXTO.md

## Orquestração dos agentes

A sessão principal é a **orquestradora**: planeja, delega, integra, roda os
testes e cuida do git. Os agentes em `.claude/agents/` fazem o trabalho
especializado e **não fazem commit** nem trocam de branch.

| Agente | Etapas | Pode editar |
|---|---|---|
| `motor-limites` | 2, 3, 4, 5 e bugs de cálculo | `backend/app/motor/`, `backend/testes/test_motor.py` |
| `revisor-matematico` | depois de cada etapa do motor | nada (só lê e executa) |
| `api-backend` | 6 e parte da 8 | `backend/app/{main.py,rotas,modelos,grafico}`, `backend/testes/test_api.py` |
| `frontend-web` | 7 e 8 | `frontend/` |

### Fluxo de cada etapa do motor (2 a 5)

1. Orquestradora cria `feature/etapa-N-nome-curto` a partir da etapa anterior
   (ou da `main` atualizada, se já foi mesclada).
2. Delega **uma técnica por vez** ao `motor-limites`, com o escopo e os
   exemplos esperados no prompt.
3. Roda `cd backend && .venv/bin/pytest -q`. Se falhar, devolve ao agente com a
   saída real.
4. Passa o resultado ao `revisor-matematico`, dizendo a etapa e a técnica.
5. Achados de erro matemático voltam ao `motor-limites`. Explicação confusa
   também. Repete 3 e 4 até o revisor não apontar problemas graves.
6. Orquestradora faz o commit (um por técnica) e, ao fim da etapa, o push da
   branch.

### Etapas de API e página (6 a 8)

- `api-backend` e `frontend-web` dependem do contrato de resposta
  (`backend/app/modelos/schemas.py`). Fixe o contrato primeiro, com o
  `api-backend`, e só então acione o `frontend-web`.
- Os dois só podem trabalhar em paralelo depois do contrato fechado, porque
  editam pastas diferentes. O motor nunca roda em paralelo com outro agente que
  edite o mesmo arquivo.
- A orquestradora testa a integração de verdade (servidor no ar e chamadas
  reais) antes de dar a etapa por concluída.

### Regras gerais

- Uma branch por feature; commits pequenos em português com a linha de
  co-autoria; nada de merge na `main` nem force push sem pedido explícito.
- Ao delegar, dê contexto completo no prompt (o agente começa sem memória da
  conversa): etapa, arquivos, exemplos de entrada e saída esperados, e o que
  não deve ser alterado.
- Ao receber o relatório de um agente, confira o que mudou (`git diff`) em vez
  de confiar só no resumo.
- Atualize `CONTEXTO.md` (seção "Estado atual") ao concluir cada etapa.
