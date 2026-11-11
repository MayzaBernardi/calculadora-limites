"""Técnicas de resolução. Aqui só se aplica a técnica; os passos ficam em passos.py."""
from dataclasses import dataclass

import sympy as sp

from app.motor.entrada import x
from app.motor.formas import lados_definidos, limite_da_parte

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


@dataclass
class TermoDominante:
    polinomio: sp.Expr          # polinômio original, expandido
    grau: int                   # grau do termo que domina (0: polinômio constante)
    coeficiente_lider: sp.Expr  # coeficiente desse termo
    termo: sp.Expr              # o termo de maior grau (coeficiente_lider · x**grau)
    valor: sp.Expr              # oo, -oo, ou o próprio valor (caso constante)


def termo_dominante(expressao: sp.Expr, ponto: sp.Expr) -> TermoDominante | None:
    """Polinômio puro em x com x -> +oo ou x -> -oo: o termo de maior grau
    "domina" o comportamento (os de grau menor ficam desprezíveis), então o
    limite do polinômio é o limite desse termo. O sinal do resultado vem do
    coeficiente líder, da paridade do grau e do sentido do infinito: se x ->
    +oo, x**grau é sempre positivo; se x -> -oo, x**grau é positivo quando o
    grau é par e negativo quando é ímpar. Polinômio constante (sem x depois de
    expandir) é um caso trivial, sem termo que domine: o valor não depende de
    x. Devolve None se a técnica não se aplica."""
    if ponto not in (sp.oo, -sp.oo) or not expressao.is_polynomial(x):
        return None
    polinomio = sp.expand(expressao)
    if not polinomio.has(x):
        return TermoDominante(polinomio, 0, polinomio, polinomio, polinomio)
    poly = sp.Poly(polinomio, x)
    grau = poly.degree()
    coeficiente = poly.LC()
    termo = coeficiente * x**grau
    sinal_coeficiente = 1 if coeficiente.is_positive else -1
    sinal_xn = 1 if ponto == sp.oo or grau % 2 == 0 else -1
    valor = sp.oo if sinal_coeficiente * sinal_xn > 0 else -sp.oo
    return TermoDominante(polinomio, grau, coeficiente, termo, valor)


@dataclass
class Bloco:
    lado: str                   # "numerador" ou "denominador"
    nome: str                   # nome curto para a explicação
    u: sp.Expr                  # argumento que tende a 0
    g: sp.Expr                  # o fator reconhecido, ex.: sen(3x)
    h: sp.Expr                  # com o que ele se compara, ex.: 3x (ou u²)
    valor: sp.Expr              # limite de g/h quando u -> 0
    formula: str                # o limite fundamental em LaTeX


@dataclass
class Fundamentais:
    numerador: sp.Expr
    denominador: sp.Expr
    blocos: list[Bloco]
    fator: sp.Expr              # produto dos limites fundamentais (valor1 / valor2)
    resto: sp.Expr              # o que sobra para calcular
    valor_denominador: sp.Expr | None = None  # valor do bloco do denominador


def _bloco_de(fator: sp.Expr, lado: str) -> Bloco | None:
    """Reconhece um dos limites fundamentais em um fator, ou None."""
    if fator.func in (sp.sin, sp.tan):
        u = fator.args[0]
        nome = "sen" if fator.func == sp.sin else "tg"
        letra = r"\sin" if fator.func == sp.sin else r"\tan"
        return Bloco(lado, nome, u, fator, u, sp.Integer(1),
                     rf"\lim_{{u \to 0}} \frac{{{letra} u}}{{u}} = 1")
    if fator.is_Pow and fator.exp == 2 and fator.base.func == sp.sin:
        u = fator.base.args[0]
        return Bloco(lado, "sen²", u, fator, u**2, sp.Integer(1),
                     r"\lim_{u \to 0} \frac{\sin^{2} u}{u^{2}} = 1")
    if fator.func == sp.log:
        u = fator.args[0] - 1
        return Bloco(lado, "ln(1+u)", u, fator, u, sp.Integer(1),
                     r"\lim_{u \to 0} \frac{\ln(1 + u)}{u} = 1")
    if fator.is_Add and len(fator.args) == 2:
        if sp.Integer(-1) in fator.args:
            outro = [a for a in fator.args if a != -1][0]
            if outro.func == sp.exp:
                u = outro.args[0]
                return Bloco(lado, "e^u-1", u, fator, u, sp.Integer(1),
                             r"\lim_{u \to 0} \frac{e^{u} - 1}{u} = 1")
            if (outro.is_Pow and outro.base.is_number and outro.base.is_positive
                    and outro.base != 1 and outro.exp.has(x)):
                u = outro.exp
                return Bloco(lado, "a^u-1", u, fator, u, sp.log(outro.base),
                             rf"\lim_{{u \to 0}} \frac{{{sp.latex(outro.base)}^{{u}} - 1}}{{u}}"
                             rf" = {sp.latex(sp.log(outro.base), ln_notation=True)}")
        if sp.Integer(-1) in fator.args:
            outro = [a for a in fator.args if a != -1][0]
            if outro.func == sp.cos:
                u = outro.args[0]
                return Bloco(lado, "cos-1", u, fator, u**2, -sp.Rational(1, 2),
                             r"\lim_{u \to 0} \frac{\cos u - 1}{u^{2}} = -\frac{1}{2}")
        if sp.Integer(1) in fator.args:
            outro = [a for a in fator.args if a != 1][0]
            if outro.is_Mul and len(outro.args) == 2 and outro.args[0] == -1 \
                    and outro.args[1].func == sp.cos:
                u = outro.args[1].args[0]
                return Bloco(lado, "1-cos", u, fator, u**2, sp.Rational(1, 2),
                             r"\lim_{u \to 0} \frac{1 - \cos u}{u^{2}} = \frac{1}{2}")
    return None


def _acha_bloco(parte: sp.Expr, lado: str, ponto: sp.Expr, lados: list):
    """Procura em `parte` (um produto) um fator fundamental com u -> 0 em todos
    os `lados` onde a função existe. Devolve (bloco, demais fatores) ou
    (None, parte)."""
    fatores = list(sp.Mul.make_args(parte))
    for i, fator in enumerate(fatores):
        bloco = _bloco_de(fator, lado)
        if bloco is None or not bloco.u.has(x):
            continue
        if all(limite_da_parte(bloco.u, ponto, l) == 0 for l in lados):
            return bloco, sp.Mul(*(fatores[:i] + fatores[i + 1:]))
    return None, parte


def aplicar_limites_fundamentais(
    expressao: sp.Expr, ponto: sp.Expr
) -> Fundamentais | None:
    """Reconhece sen u/u, tg u/u, (e^u-1)/u, ln(1+u)/u, (1-cos u)/u², sen²u/u²
    e (a^u-1)/u com u -> 0, no numerador e/ou no denominador. Reescreve
    N/D = [g1/h1 ÷ g2/h2] · [h1·resto1 / (h2·resto2)] e devolve o fator
    fundamental e o resto, que o resolvedor calcula em seguida. u precisa
    tender a 0 por todos os lados em que a função existe."""
    if sp.count_ops(expressao) > 100:
        return None
    numerador, denominador = sp.fraction(expressao)
    if denominador == 1:
        return None
    lados = lados_definidos(expressao, ponto) if ponto.is_finite else [None]
    if not lados:
        return None
    bloco_n, resto_n = _acha_bloco(numerador, "numerador", ponto, lados)
    bloco_d, resto_d = _acha_bloco(denominador, "denominador", ponto, lados)
    if bloco_n is None and bloco_d is None:
        return None
    um = sp.Integer(1)
    h_n, v_n = (bloco_n.h, bloco_n.valor) if bloco_n else (um, um)
    h_d, v_d = (bloco_d.h, bloco_d.valor) if bloco_d else (um, um)
    resto = h_n * resto_n / (h_d * resto_d)
    if not resto.atoms(sp.Function):
        resto = sp.cancel(sp.together(resto))  # com funções, o cancel desfaria os fatores
    if resto == expressao or resto.has(sp.nan, sp.zoo, sp.oo):
        return None
    blocos = [b for b in (bloco_n, bloco_d) if b is not None]
    fator = sp.expand_log(v_n / v_d, force=True)
    return Fundamentais(numerador, denominador, blocos, fator, resto,
                        v_d if bloco_d else None)
