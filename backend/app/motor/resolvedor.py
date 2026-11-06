"""Fluxo principal: decide qual técnica usar e registra os passos."""
from dataclasses import dataclass, field

import sympy as sp

from app.motor import passos
from app.motor.entrada import x
from app.motor.formas import definida_no_lado, identificar_forma
from app.motor.passos import Passo
from app.motor.seguro import limite_seguro
from app.motor.tecnicas import fatorar_e_cancelar, racionalizar

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


def _tem_zero_elevado_a_zero(expressao: sp.Expr, ponto: sp.Expr) -> bool:
    """O SymPy diz 0**0 = 1, mas para limites 0^0 é indeterminação."""
    for potencia in expressao.atoms(sp.Pow):
        base = potencia.base.subs(x, ponto)
        expoente = potencia.exp.subs(x, ponto)
        if base == 0 and expoente == 0:
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
        lados = [l for l in ("+", "-") if definida_no_lado(expressao, ponto, l)]
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
) -> Resultado:
    """Resolve a expressão transformada por uma técnica e confere com o SymPy.
    Se a técnica não conclui, ou o valor diverge do sp.limit, descarta os
    passos da técnica e acrescenta um passo honesto no lugar."""
    sub = resolver(nova, ponto, profundidade + 1)
    if not (sub.resolvido and sub.existe):
        return Resultado(
            resolvido=False, passos=base + [passos.passo_tecnica_sem_conclusao(False)]
        )
    validado = conferir_com_sympy(original, ponto, sub.valor)
    if validado is False:
        return Resultado(
            resolvido=False, validado=False,
            passos=base + [passos.passo_tecnica_sem_conclusao(True)],
        )
    lista = base + passos_tecnica + sub.passos[1:]  # o 1º repete o limite já mostrado
    lista.append(passos.passo_resultado(original, ponto, sub.valor))
    return Resultado(
        resolvido=True, existe=True, valor=sub.valor, passos=lista, validado=validado
    )


def _decimais_para_racionais(expr: sp.Expr) -> sp.Expr:
    """0.5 vira 1/2: a entrada decimal é exata para o aluno."""
    return expr.xreplace({f: sp.Rational(str(f)) for f in expr.atoms(sp.Float)})


def resolver(expressao: sp.Expr, ponto: sp.Expr, profundidade: int = 0) -> Resultado:
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
            return _continuar(
                expressao, ponto, fatoracao.simplificada, lista, tecnica, profundidade)

        racionalizacao = racionalizar(expressao, ponto)
        if racionalizacao is not None:
            tecnica = [
                passos.passo_conjugado(racionalizacao),
                passos.passo_multiplicacao_conjugado(expressao, ponto, racionalizacao),
                passos.passo_simplificacao_racionalizacao(
                    expressao, ponto, racionalizacao),
            ]
            return _continuar(
                expressao, ponto, racionalizacao.simplificada, lista, tecnica,
                profundidade)

    # As próximas etapas (laterais, infinito, L'Hôpital...) entram aqui.
    return Resultado(resolvido=False, passos=lista)
