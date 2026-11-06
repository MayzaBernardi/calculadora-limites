"""Técnicas de resolução. Aqui só se aplica a técnica; os passos ficam em passos.py."""
from dataclasses import dataclass

import sympy as sp

from app.motor.entrada import x

# Acima disso o factor do SymPy fica lento demais (grau 300 leva ~5 s; grau 100 leva menos de 1 s).
GRAU_MAXIMO = 100


@dataclass
class Fatoracao:
    numerador: sp.Expr          # numerador fatorado
    denominador: sp.Expr        # denominador fatorado
    fator_comum: sp.Expr        # fator que zera no ponto e será cancelado
    simplificada: sp.Expr       # expressão depois do cancelamento


def fatorar_e_cancelar(expressao: sp.Expr, ponto: sp.Expr) -> Fatoracao | None:
    """Fatora numerador e denominador de uma função racional e cancela o fator
    comum que se anula em `ponto`. Devolve None se a técnica não se aplica."""
    if not ponto.is_finite:
        return None
    numerador, denominador = sp.fraction(expressao)
    if denominador == 1 and expressao.is_Add:
        # together() já cancela fatores, então só entra quando não há fração explícita
        numerador, denominador = sp.fraction(sp.together(expressao))
    if not (numerador.is_polynomial(x) and denominador.is_polynomial(x)):
        return None
    if denominador.is_number:
        return None
    if max(sp.degree(numerador, x), sp.degree(denominador, x)) > GRAU_MAXIMO:
        return None
    comum = sp.gcd(numerador, denominador)
    if not comum.has(x) or sp.simplify(comum.subs(x, ponto)) != 0:
        return None
    num_fat = sp.factor(numerador)
    den_fat = sp.factor(denominador)
    simplificada = sp.cancel(sp.Mul(num_fat, 1 / den_fat, evaluate=False))
    if simplificada == expressao:
        return None
    # Fator mônico (x - 2 em vez de 2x - 4), mais legível no passo a passo.
    fator = sp.Poly(comum, x).monic().as_expr()
    return Fatoracao(num_fat, den_fat, fator, simplificada)


@dataclass
class Racionalizacao:
    alvo: str                   # "numerador" ou "denominador"
    com_raiz: sp.Expr           # fator binomial com raiz que se anula no ponto
    com_raiz_exib: sp.Expr      # o mesmo, na ordem em que aparece escrito
    conjugado: sp.Expr
    conjugado_exib: sp.Expr     # conjugado com os termos na mesma ordem
    primeiro: sp.Expr           # P em (P - Q)(P + Q)
    segundo: sp.Expr            # Q
    produto: sp.Expr            # P² - Q², já simplificado
    numerador: sp.Expr          # numerador depois de multiplicar
    denominador: sp.Expr        # denominador depois de multiplicar
    simplificada: sp.Expr       # expressão depois de cancelar
    fator_cancelado: sp.Expr | None  # fator comum que foi cancelado
    outros_fatores: sp.Expr     # o que multiplica o fator com raiz no mesmo lado
    raiz_nos_dois_lados: bool   # a outra parte da fração ainda tem raiz


def _tem_raiz(parte: sp.Expr) -> bool:
    """Há potência de expoente fracionário que depende de x?"""
    return any(
        p.exp.is_Rational and not p.exp.is_Integer and p.has(x)
        for p in parte.atoms(sp.Pow)
    )


def _raizes_quadradas_de_polinomios(parte: sp.Expr) -> bool:
    """Todas as raízes que dependem de x são sqrt de polinômio?"""
    for p in parte.atoms(sp.Pow):
        if p.has(x) and p.exp.is_Rational and not p.exp.is_Integer:
            if p.exp != sp.Rational(1, 2) or not p.base.is_polynomial(x):
                return False
    return True


def _binomio_que_zera(lado: sp.Expr, ponto: sp.Expr):
    """Acha, em `lado` (produto de fatores), o único binômio com raiz que se
    anula em `ponto`. Devolve (binômio, demais fatores) ou None."""
    candidatos = []
    for fator in sp.Mul.make_args(lado):
        if fator.is_Add and len(fator.args) == 2 and _tem_raiz(fator):
            if sp.simplify(fator.subs(x, ponto)) == 0:
                candidatos.append(fator)
    if len(candidatos) != 1:
        return None
    demais = [f for f in sp.Mul.make_args(lado) if f is not candidatos[0]]
    return candidatos[0], sp.Mul(*demais)


def racionalizar(expressao: sp.Expr, ponto: sp.Expr) -> Racionalizacao | None:
    """Multiplica pelo conjugado do binômio com raiz quadrada que zera no ponto.
    Se há raiz no numerador e no denominador, começa pelo numerador; a nova
    expressão volta ao resolvedor, que racionaliza o denominador na sequência.
    Devolve None (sem erro) se a técnica não se aplica."""
    if not ponto.is_finite or sp.count_ops(expressao) > 100:
        return None
    if expressao.atoms(sp.Function) or not _raizes_quadradas_de_polinomios(expressao):
        return None
    numerador, denominador = sp.fraction(expressao)
    if denominador == 1:
        return None
    raiz_num, raiz_den = _tem_raiz(numerador), _tem_raiz(denominador)
    if not (raiz_num or raiz_den):
        return None
    achado = _binomio_que_zera(numerador, ponto) if raiz_num else None
    alvo = "numerador"
    if achado is None:
        achado = _binomio_que_zera(denominador, ponto) if raiz_den else None
        alvo = "denominador"
    if achado is None:
        return None
    binomio, resto = achado
    outra = denominador if alvo == "numerador" else numerador

    termos = binomio.as_ordered_terms()
    t1, t2 = termos
    neg1, neg2 = t1.could_extract_minus_sign(), t2.could_extract_minus_sign()
    if neg1 and neg2:
        return None
    # O conjugado troca o sinal do termo que vem subtraído (ou do 2º, numa soma),
    # de modo que binômio · conjugado = primeiro² − segundo².
    if neg2:
        primeiro, segundo, termos_conj = t1, -t2, (t1, -t2)
    elif neg1:
        primeiro, segundo, termos_conj = t2, -t1, (-t1, t2)
    else:
        primeiro, segundo, termos_conj = t1, t2, (t1, -t2)
    conjugado = sp.Add(*termos_conj)
    conjugado_exib = sp.Add(*termos_conj, evaluate=False)

    produto = sp.expand(primeiro**2 - segundo**2)
    if _tem_raiz(produto) or not produto.is_polynomial(x) or produto == 0:
        return None

    if alvo == "numerador":
        novo_num = sp.Mul(resto, produto)
        novo_den = sp.Mul(outra, conjugado, evaluate=False)
    else:
        novo_num = sp.Mul(outra, conjugado, evaluate=False)
        novo_den = sp.Mul(resto, produto)
    # Cancela só o fator polinomial comum (o SymPy não cancela direito quando x e
    # sqrt(x) aparecem juntos); sem polinômio, mantém o produto sem cancelar.
    fator = None
    fora, dentro = outra, produto  # fator de `outra` e o produto notável
    if outra.is_polynomial(x):
        comum = sp.gcd(produto, outra)
        if comum.has(x):
            fator = comum
            fora, dentro = sp.cancel(outra / comum), sp.cancel(produto / comum)
    if alvo == "numerador":
        simplificada = sp.Mul(resto, dentro) / sp.Mul(fora, conjugado)
    else:
        simplificada = sp.Mul(fora, conjugado) / sp.Mul(resto, dentro)
    if simplificada == expressao:
        return None
    return Racionalizacao(
        alvo, binomio, sp.Add(*termos, evaluate=False), conjugado, conjugado_exib,
        primeiro, segundo, produto, novo_num, novo_den, simplificada, fator,
        resto, _tem_raiz(outra),
    )
