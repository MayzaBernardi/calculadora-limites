"""Fluxo principal: decide qual técnica usar e registra os passos."""
from dataclasses import dataclass, field

import sympy as sp

from app.motor import passos
from app.motor.entrada import x
from app.motor.formas import identificar_forma, lados_definidos
from app.motor.laterais import analisar_sinais, calcular_laterais, concluir
from app.motor.passos import Passo
from app.motor.seguro import limite_seguro
from app.motor.tecnicas import (
    aplicar_limites_fundamentais, divisao_maior_potencia, fatorar_e_cancelar,
    limitada_sobre_infinito, racionalizar, termo_dominante,
)

PROFUNDIDADE_MAXIMA = 5

# Funções descontínuas: a substituição direta não vale para elas.
FUNCOES_DESCONTINUAS = (sp.floor, sp.ceiling, sp.sign)


@dataclass
class Resultado:
    resolvido: bool
    existe: bool | None = None
    valor: sp.Expr | None = None
    passos: list[Passo] = field(default_factory=list)
    validado: bool | None = None  # conferido com sp.limit (None: não conferido)
    esquerda: sp.Expr | None = None  # limite lateral (ponto finito)
    direita: sp.Expr | None = None


def _tem_zero_elevado_a_zero(expressao: sp.Expr, ponto: sp.Expr) -> bool:
    """O SymPy diz 0**0 = 1, mas para limites 0^0 é indeterminação."""
    for potencia in expressao.atoms(sp.Pow):
        base = potencia.base.subs(x, ponto)
        expoente = potencia.exp.subs(x, ponto)
        if base == 0 and expoente == 0:
            return True
    return False


def _pode_sair_dos_reais(expressao: sp.Expr) -> bool:
    """Polinômios, quocientes, sen, cos, e^x... são reais onde existem. Só
    logaritmo, potência de expoente não inteiro e afins podem dar não real."""
    seguras = (sp.sin, sp.cos, sp.tan, sp.exp, sp.Abs, sp.floor, sp.ceiling, sp.sign)
    for parte in sp.preorder_traversal(expressao):
        if parte.is_Pow and not parte.exp.is_Integer and parte.base != sp.E:
            return True
        if parte.is_Function and not isinstance(parte, seguras):
            return True
    return False


def substituir(expressao: sp.Expr, ponto: sp.Expr) -> tuple[sp.Expr | None, str]:
    """Tenta f(ponto). Devolve (valor, "") ou (None, motivo da falha)."""
    if expressao.has(*FUNCOES_DESCONTINUAS):
        return None, "a função tem saltos (piso, teto ou sinal), então não vale substituir."
    if _tem_zero_elevado_a_zero(expressao, ponto):
        return None, "aparece 0^0, que é uma indeterminação."
    valor = sp.simplify(expressao.subs(x, ponto))
    if valor.has(sp.nan):
        return None, "aparece uma indeterminação (como 0/0)."
    if valor.has(sp.zoo, sp.oo, -sp.oo):
        return None, "aparece uma divisão por zero ou um valor infinito."
    if valor.has(sp.I) or valor.is_real is False:
        return None, "o ponto está fora do domínio da função (resultado não real)."
    if _pode_sair_dos_reais(expressao) and lados_definidos(expressao, ponto) == []:
        # f(ponto) dá real por coincidência, mas a função não é real ao redor
        return None, (
            "a conta dá um número, mas a função não está definida (nos reais) "
            "nem à esquerda nem à direita do ponto, então não há limite a calcular."
        )
    return valor, ""


TAMANHO_MAXIMO_CONFERENCIA = 300  # acima disso (sp.count_ops) não conferimos


def conferir_com_sympy(
    expressao: sp.Expr, ponto: sp.Expr, valor: sp.Expr, lado: str = "+-"
) -> bool | None:
    """Compara o valor com sp.limit. `lado` é "+", "-" ou "+-" (os dois lados,
    padrão); use "+" ou "-" para limites de um lado só. Devolve None se a
    expressão for grande demais ou se o SymPy não conseguir calcular."""
    if sp.count_ops(expressao) > TAMANHO_MAXIMO_CONFERENCIA:
        return None
    if lado == "+-" and ponto.is_finite:
        # função definida só de um lado: compara com o limite desse lado
        lados = lados_definidos(expressao, ponto)
        if lados is None:
            return None
        if len(lados) == 1:
            lado = lados[0]
    esperado = limite_seguro(expressao, ponto, lado if ponto.is_finite else None)
    if esperado is None or esperado.has(sp.nan, sp.zoo, sp.AccumBounds):
        return None
    if esperado == valor:
        return True
    if esperado.is_infinite or valor.is_infinite:
        return False
    return bool(sp.simplify(esperado - valor) == 0)


def _continuar(
    original: sp.Expr, ponto: sp.Expr, nova: sp.Expr, base: list[Passo],
    passos_tecnica: list[Passo], profundidade: int,
    multiplicador: sp.Expr = sp.Integer(1),
) -> Resultado:
    """Resolve a expressão transformada por uma técnica e confere com o SymPy.
    Se a técnica não conclui, ou o valor diverge do sp.limit, descarta os
    passos da técnica e acrescenta um passo honesto no lugar."""
    sub = resolver(nova, ponto, profundidade + 1)
    if not (sub.resolvido and sub.existe):
        return Resultado(
            resolvido=False, passos=base + [passos.passo_tecnica_sem_conclusao("sem_conclusao")]
        )
    valor = sp.simplify(multiplicador * sub.valor)
    validado = conferir_com_sympy(original, ponto, valor)
    if validado is False:
        return Resultado(
            resolvido=False, validado=False,
            passos=base + [passos.passo_tecnica_sem_conclusao("divergiu")],
        )
    if validado is None and ponto.is_finite:
        # sem confirmação independente não afirmamos o valor de uma técnica
        return Resultado(
            resolvido=False,
            passos=base + [passos.passo_tecnica_sem_conclusao("nao_confirmado")],
        )
    lista = base + passos_tecnica + sub.passos[1:]  # o 1º repete o limite já mostrado
    lista.append(passos.passo_resultado(original, ponto, valor))
    return Resultado(
        resolvido=True, existe=True, valor=valor, passos=lista, validado=validado
    )


def _por_laterais(expressao: sp.Expr, ponto: sp.Expr, base: list[Passo]) -> Resultado | None:
    """Compara os limites laterais (só os lados onde a função existe). Cobre
    k/0 (com análise de sinal), laterais diferentes e domínio de um lado só."""
    if not ponto.is_finite:
        return None
    laterais = calcular_laterais(expressao, ponto)
    if laterais is None:
        return None
    conclusao = concluir(laterais)
    lista = base + [passos.passo_laterais(expressao, ponto, laterais)]
    analises = analisar_sinais(expressao, ponto, laterais)
    if analises:
        lista.append(passos.passo_analise_de_sinal(expressao, ponto, analises))
    lista.append(passos.passo_conclusao_laterais(expressao, ponto, laterais, conclusao))
    return Resultado(
        resolvido=True, existe=conclusao.existe, valor=conclusao.valor, passos=lista,
        validado=True if analises else None,
        esquerda=laterais.esquerda, direita=laterais.direita,
    )


def _ou_laterais(
    falha: Resultado, expressao: sp.Expr, ponto: sp.Expr, base: list[Passo]
) -> Resultado:
    """Se a técnica resolveu, devolve o resultado dela; senão tenta os laterais
    (sem os passos descartados da técnica) e, se também não der, devolve a falha.
    Quando a técnica divergiu do SymPy (validado False), mantém a falha honesta."""
    if falha.resolvido or falha.validado is False:
        return falha  # divergência com o SymPy não se esconde atrás dos laterais
    return _por_laterais(expressao, ponto, base) or falha


def _decimais_para_racionais(expr: sp.Expr) -> sp.Expr:
    """0.5 vira 1/2: a entrada decimal é exata para o aluno."""
    return expr.xreplace({f: sp.Rational(str(f)) for f in expr.atoms(sp.Float)})


def _preencher_laterais(resultado: Resultado, expressao: sp.Expr, ponto: sp.Expr) -> Resultado:
    """Garante os laterais no resultado final de um ponto finito (a API os mostra)."""
    if not (ponto.is_finite and resultado.resolvido and resultado.existe):
        return resultado
    if resultado.esquerda is None and resultado.direita is None:
        # o limite existe: vale o mesmo em cada lado onde a função está definida
        lados = lados_definidos(expressao, ponto) or []
        if "-" in lados:
            resultado.esquerda = resultado.valor
        if "+" in lados:
            resultado.direita = resultado.valor
    return resultado


def resolver(expressao: sp.Expr, ponto: sp.Expr, profundidade: int = 0) -> Resultado:
    resultado = _resolver(expressao, ponto, profundidade)
    if profundidade == 0:
        resultado = _preencher_laterais(
            resultado, _decimais_para_racionais(expressao), _decimais_para_racionais(ponto))
    return resultado


def _resolver(expressao: sp.Expr, ponto: sp.Expr, profundidade: int) -> Resultado:
    if profundidade == 0:
        expressao = _decimais_para_racionais(expressao)
        ponto = _decimais_para_racionais(ponto)
    lista = [passos.passo_funcao_dada(expressao, ponto)]

    if ponto.is_finite:
        valor, motivo = substituir(expressao, ponto)
        if valor is not None:
            lista.append(passos.passo_substituicao_direta(expressao, ponto, valor))
            return Resultado(resolvido=True, existe=True, valor=valor, passos=lista)
        lista.append(passos.passo_substituicao_sem_resultado(expressao, ponto, motivo))

    if not ponto.is_finite:
        # Polinômio puro: o termo de maior grau decide, sem depender de
        # "forma" (que classificaria x**3 - x como "oo-oo" por engano, já
        # que o termo dominante sempre resolve um polinômio nesse caso).
        dominante = termo_dominante(expressao, ponto)
        if dominante is not None:
            tecnica = [passos.passo_termo_dominante(expressao, ponto, dominante)]
            validado = conferir_com_sympy(expressao, ponto, dominante.valor)
            if validado:
                lista_final = lista + tecnica
                lista_final.append(passos.passo_resultado(expressao, ponto, dominante.valor))
                return Resultado(
                    resolvido=True, existe=True, valor=dominante.valor,
                    passos=lista_final, validado=True,
                )
            motivo_falha = "divergiu" if validado is False else "nao_confirmado"
            return Resultado(
                resolvido=False, validado=validado,
                passos=lista + tecnica + [passos.passo_tecnica_sem_conclusao(motivo_falha)],
            )

        # Não é polinômio puro: pode ser uma função racional (quociente de
        # polinômios), que é resolvida dividindo pela maior potência.
        divisao = divisao_maior_potencia(expressao, ponto)
        if divisao is not None:
            tecnica = [
                passos.passo_divisao_maior_potencia(expressao, ponto, divisao),
                passos.passo_conclusao_divisao_maior_potencia(expressao, ponto, divisao),
            ]
            validado = conferir_com_sympy(expressao, ponto, divisao.valor)
            if validado:
                lista_final = lista + tecnica
                lista_final.append(passos.passo_resultado(expressao, ponto, divisao.valor))
                return Resultado(
                    resolvido=True, existe=True, valor=divisao.valor,
                    passos=lista_final, validado=True,
                )
            motivo_falha = "divergiu" if validado is False else "nao_confirmado"
            return Resultado(
                resolvido=False, validado=validado,
                passos=lista + tecnica + [passos.passo_tecnica_sem_conclusao(motivo_falha)],
            )

        # Nem polinômio puro, nem função racional: pode ser um numerador
        # limitado (sen, cos, constantes...) sobre algo que cresce sem
        # limite, caso em que o teorema do confronto dá o limite 0.
        limitada = limitada_sobre_infinito(expressao, ponto)
        if limitada is not None:
            tecnica = [
                passos.passo_funcao_limitada(expressao, ponto, limitada),
                passos.passo_confronto_limitada_sobre_infinito(expressao, ponto, limitada),
            ]
            validado = conferir_com_sympy(expressao, ponto, limitada.valor)
            if validado:
                lista_final = lista + tecnica
                lista_final.append(passos.passo_resultado(expressao, ponto, limitada.valor))
                return Resultado(
                    resolvido=True, existe=True, valor=limitada.valor,
                    passos=lista_final, validado=True,
                )
            motivo_falha = "divergiu" if validado is False else "nao_confirmado"
            return Resultado(
                resolvido=False, validado=validado,
                passos=lista + tecnica + [passos.passo_tecnica_sem_conclusao(motivo_falha)],
            )

    forma = identificar_forma(expressao, ponto)
    if forma is not None:
        lista.append(passos.passo_forma_indeterminada(expressao, ponto, forma))

    if forma == "0/0" and profundidade < PROFUNDIDADE_MAXIMA:
        fatoracao = fatorar_e_cancelar(expressao, ponto)
        if fatoracao is not None:
            tecnica = [
                passos.passo_fatoracao(
                    expressao, ponto, fatoracao.numerador, fatoracao.denominador,
                    fatoracao.fator_comum),
                passos.passo_cancelamento(
                    fatoracao.fator_comum, fatoracao.simplificada,
                    fatoracao.numerador, fatoracao.denominador, ponto),
            ]
            falha = _continuar(
                expressao, ponto, fatoracao.simplificada, lista, tecnica, profundidade)
            return _ou_laterais(falha, expressao, ponto, lista)

        racionalizacao = racionalizar(expressao, ponto)
        if racionalizacao is not None:
            tecnica = [
                passos.passo_conjugado(racionalizacao),
                passos.passo_multiplicacao_conjugado(expressao, ponto, racionalizacao),
                passos.passo_simplificacao_racionalizacao(
                    expressao, ponto, racionalizacao),
            ]
            falha = _continuar(
                expressao, ponto, racionalizacao.simplificada, lista, tecnica,
                profundidade)
            return _ou_laterais(falha, expressao, ponto, lista)

        fundamentais = aplicar_limites_fundamentais(expressao, ponto)
        if fundamentais is not None:
            tecnica = [passos.passo_limite_fundamental(b, ponto) for b in fundamentais.blocos]
            tecnica.append(passos.passo_ajuste_fundamental(expressao, ponto, fundamentais))
            tecnica.append(passos.passo_produto_de_limites(expressao, ponto, fundamentais))
            falha = _continuar(
                expressao, ponto, fundamentais.resto, lista, tecnica, profundidade,
                multiplicador=fundamentais.fator)
            return _ou_laterais(falha, expressao, ponto, lista)

    # As próximas etapas (infinito, L'Hôpital...) entram aqui.
    return _ou_laterais(Resultado(resolvido=False, passos=lista), expressao, ponto, lista)
