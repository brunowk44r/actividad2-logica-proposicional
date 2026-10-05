#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sistema_reglas_proposicional.py
Recibe hechos explícitos (literales) y reglas R1, R2, ... cuyo antecedente es un
literal o una conjunción de literales y cuya conclusión es un literal.
Aplica encadenamiento hacia adelante con traza, detecta conflictos y reporta el
estado de la decisión: conclusión obtenida / sin conclusión / conflicto.
Uso: python sistema_reglas_proposicional.py [original|prueba|corregida] [E1 E2 ...]

Actividad 2 - Fundamentos de Inteligencia Artificial (E-FIA-3), UPP
Alumno: Bruno Huerta Morales   Docente: Dr. Jaime Aguilar Ortiz
No requiere paquetes adicionales (solo biblioteca estándar de Python 3).
"""
# ===================================================================
# LECTOR DE FÓRMULAS (mismo diseño en los tres programas)
# -------------------------------------------------------------------
# Escritura de teclado acordada en clase:
#     ~    negación            ~p
#     &    conjunción          (p & q)
#     |    disyunción          (p | q)
#     ->   implicación         (p -> q)
#     <->  bicondicional       (p <-> q)
# Las variables son letras minúsculas (pueden llevar dígitos o _, ej. p1).
# Precedencia (de mayor a menor): ~, &, |, ->, <->.  La implicación
# agrupa a la derecha:  p -> q -> r  se lee  p -> (q -> r).
# Se recomienda escribir con paréntesis, como pide el taller: ((p & q) -> r)
#
# El lector NO usa eval(): separa símbolos (tokens), construye un árbol
# y evalúa primero las partes internas y después el conectivo exterior.
# ===================================================================
import itertools


class ErrorFormula(Exception):
    """Error de escritura en una fórmula; el mensaje explica la causa."""


SIMBOLOS = {"~": "NOT", "&": "AND", "|": "OR", "->": "IMP", "<->": "IFF",
            "(": "LPAR", ")": "RPAR"}
TEXTO_OP = {"AND": "&", "OR": "|", "IMP": "->", "IFF": "<->"}


def separar_simbolos(texto):
    """Convierte el texto en una lista de (tipo, valor, posición)."""
    tokens = []
    i = 0
    while i < len(texto):
        c = texto[i]
        if c.isspace():
            i += 1
        elif texto.startswith("<->", i):
            tokens.append(("IFF", "<->", i)); i += 3
        elif texto.startswith("->", i):
            tokens.append(("IMP", "->", i)); i += 2
        elif c in "~&|()":
            tokens.append((SIMBOLOS[c], c, i)); i += 1
        elif c.isalpha() and c.islower():
            j = i
            while j < len(texto) and (texto[j].isalnum() or texto[j] == "_"):
                j += 1
            tokens.append(("VAR", texto[i:j], i)); i = j
        else:
            raise ErrorFormula(
                f"símbolo no permitido '{c}' en la posición {i + 1}. "
                "Use ~ & | -> <-> ( ) y letras minúsculas.")
    if not tokens:
        raise ErrorFormula("la fórmula está vacía.")
    return tokens


class _Analizador:
    """Analizador recursivo: cada nivel corresponde a un conectivo."""

    def __init__(self, tokens):
        self.t = tokens
        self.i = 0

    def ver(self):
        return self.t[self.i][0] if self.i < len(self.t) else "FIN"

    def tomar(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def formula(self):
        arbol = self.bicondicional()
        if self.ver() == "RPAR":
            raise ErrorFormula("hay un paréntesis ')' que no fue abierto.")
        if self.ver() != "FIN":
            _, valor, pos = self.t[self.i]
            raise ErrorFormula(f"falta un conectivo antes de '{valor}' "
                               f"(posición {pos + 1}).")
        return arbol

    def bicondicional(self):
        izq = self.implicacion()
        while self.ver() == "IFF":
            self.tomar()
            izq = ("IFF", izq, self.implicacion())
        return izq

    def implicacion(self):
        izq = self.disyuncion()
        if self.ver() == "IMP":
            self.tomar()
            return ("IMP", izq, self.implicacion())   # asociativa a la derecha
        return izq

    def disyuncion(self):
        izq = self.conjuncion()
        while self.ver() == "OR":
            self.tomar()
            izq = ("OR", izq, self.conjuncion())
        return izq

    def conjuncion(self):
        izq = self.negacion()
        while self.ver() == "AND":
            self.tomar()
            izq = ("AND", izq, self.negacion())
        return izq

    def negacion(self):
        if self.ver() == "NOT":
            self.tomar()
            return ("NOT", self.negacion())
        return self.atomo()

    def atomo(self):
        tipo = self.ver()
        if tipo == "VAR":
            return ("VAR", self.tomar()[1])
        if tipo == "LPAR":
            self.tomar()
            dentro = self.bicondicional()
            if self.ver() != "RPAR":
                raise ErrorFormula("paréntesis sin cerrar: falta ')'.")
            self.tomar()
            return dentro
        if tipo == "FIN":
            raise ErrorFormula("falta un operando al final de la fórmula.")
        _, valor, pos = self.t[self.i]
        raise ErrorFormula(f"falta un operando antes de '{valor}' "
                           f"(posición {pos + 1}).")


def leer_formula(texto):
    """Texto -> árbol.  Lanza ErrorFormula con un mensaje claro."""
    return _Analizador(separar_simbolos(texto)).formula()


def variables(arbol):
    """Conjunto de letras que aparecen en la fórmula, en orden alfabético."""
    if arbol[0] == "VAR":
        return {arbol[1]}
    return set().union(*(variables(h) for h in arbol[1:]))


def evaluar(arbol, val):
    """Valor de verdad del árbol con la valuación val (dict letra -> bool)."""
    op = arbol[0]
    if op == "VAR":
        return val[arbol[1]]
    if op == "NOT":
        return not evaluar(arbol[1], val)
    a = evaluar(arbol[1], val)
    b = evaluar(arbol[2], val)
    if op == "AND":
        return a and b
    if op == "OR":
        return a or b
    if op == "IMP":
        return (not a) or b                 # equivalencia (3): p->q ≡ ~p | q
    if op == "IFF":
        return a == b
    raise ValueError(op)


def a_texto(arbol, exterior=True):
    """Árbol -> texto con paréntesis completos (útil para encabezados)."""
    op = arbol[0]
    if op == "VAR":
        return arbol[1]
    if op == "NOT":
        return "~" + a_texto(arbol[1], False)
    s = f"{a_texto(arbol[1], False)} {TEXTO_OP[op]} {a_texto(arbol[2], False)}"
    return s if exterior else f"({s})"


def subformulas(arbol):
    """Subfórmulas compuestas en orden de cálculo (internas primero)."""
    lista = []

    def recorrer(a):
        if a[0] == "VAR":
            return
        for h in a[1:]:
            recorrer(h)
        if a not in lista:
            lista.append(a)
    recorrer(arbol)
    return lista


def valuaciones(letras):
    """Todas las combinaciones V/F en el orden de las tablas del curso
    (VV, VF, FV, FF ...): N = 2**n filas."""
    for valores in itertools.product([True, False], repeat=len(letras)):
        yield dict(zip(letras, valores))


def vf(b):
    return "V" if b else "F"
# ======================= fin del lector ============================


# ===================================================================
# MOTOR DE REGLAS CON ENCADENAMIENTO HACIA ADELANTE
# ===================================================================
# Literal = proposición o su negación, se escribe "p" o "~p".
# Regla   = antecedente (literal o conjunción de literales) -> literal.
# Una negación solo se usa si fue aportada como hecho o fue deducida.
# ===================================================================

def negar(lit):
    return lit[1:] if lit.startswith("~") else "~" + lit


def _literal(arbol, texto):
    if arbol[0] == "VAR":
        return arbol[1]
    if arbol[0] == "NOT" and arbol[1][0] == "VAR":
        return "~" + arbol[1][1]
    raise ErrorFormula(f"'{texto}': se esperaba un literal (p o ~p).")


def _conjuncion_literales(arbol, texto):
    if arbol[0] == "AND":
        return (_conjuncion_literales(arbol[1], texto)
                + _conjuncion_literales(arbol[2], texto))
    return [_literal(arbol, texto)]


class Regla:
    def __init__(self, ident, texto, palabras=""):
        arbol = leer_formula(texto)
        if arbol[0] != "IMP":
            raise ErrorFormula(f"{ident}: la regla debe tener la forma "
                               "antecedente -> conclusión.")
        self.id = ident
        self.texto = texto
        self.palabras = palabras
        self.arbol = arbol
        self.antecedente = _conjuncion_literales(arbol[1], texto)
        self.conclusion = _literal(arbol[2], texto)

    def __repr__(self):
        return f"{self.id}: {' & '.join(self.antecedente)} -> {self.conclusion}"


def encadenar(hechos, reglas):
    """Aplica las reglas habilitadas hasta que una vuelta completa no añada
    hechos nuevos.  Devuelve (conocidos, origen, traza, conflictos)."""
    for h in hechos:
        _literal(leer_formula(h), h)            # valida cada hecho
    conocidos = list(dict.fromkeys(hechos))     # sin duplicados, en orden
    origen = {h: ("hecho", None) for h in conocidos}
    traza = [(0, "-", list(conocidos), "Hechos iniciales")]
    conflictos = []
    paso = 0
    cambio = True
    while cambio:
        cambio = False
        for r in reglas:
            if all(a in conocidos for a in r.antecedente) \
                    and r.conclusion not in conocidos:
                paso += 1
                conocidos.append(r.conclusion)
                origen[r.conclusion] = ("regla", r)
                traza.append((paso, r.id, list(conocidos),
                              f"{r.id} con {', '.join(r.antecedente)} "
                              f"incorpora {r.conclusion}"))
                if negar(r.conclusion) in conocidos:
                    conflictos.append(r.conclusion.lstrip("~"))
                cambio = True
    return conocidos, origen, traza, sorted(set(conflictos))


def justificar(lit, origen, sangria="   "):
    """Cadena de justificación de un literal hasta los hechos iniciales."""
    tipo, r = origen[lit]
    if tipo == "hecho":
        return [f"{sangria}{lit}: hecho de entrada"]
    lineas = [f"{sangria}{lit}: por {r}"]
    for a in r.antecedente:
        lineas += justificar(a, origen, sangria + "   ")
    return lineas


def estado_decision(conocidos, decision, conflictos=()):
    """Cualquier par p / ~p suspende la recomendación, aunque no sea la
    decisión: la base usada ya no tiene modelos."""
    pos, neg = decision in conocidos, negar(decision) in conocidos
    if (pos and neg) or conflictos:
        return "CONFLICTO"
    if pos or neg:
        return "CONCLUSIÓN OBTENIDA"
    return "SIN CONCLUSIÓN"


def formulas_de_base(hechos, reglas):
    """Hechos y reglas como fórmulas para verificador_consistencia.py."""
    return list(hechos) + [f"({' & '.join(r.antecedente)}) -> {r.conclusion}"
                           for r in reglas]


def ejecutar(hechos, reglas, decision, frase=None, mostrar=True):
    conocidos, origen, traza, conflictos = encadenar(hechos, reglas)
    estado = estado_decision(conocidos, decision, conflictos)
    nuevas = [c for c in conocidos if c not in hechos]
    usadas = [t[1] for t in traza[1:]]
    if mostrar:
        print("Hechos iniciales :", ", ".join(hechos) if hechos else "(ninguno)")
        print("Traza de inferencia:")
        for p, rid, info, nota in traza:
            print(f"   paso {p}: {nota}")
        print("Conclusiones     :", ", ".join(nuevas) if nuevas else "(ninguna)")
        print("Reglas utilizadas:", ", ".join(usadas) if usadas else "(ninguna)")
        if conflictos:
            for x in conflictos:
                print(f"*** CONFLICTO: se obtuvieron {x} y ~{x} ***")
                print(f"  Justificación de {x}:")
                print("\n".join(justificar(x, origen, "     ")))
                print(f"  Justificación de ~{x}:")
                print("\n".join(justificar("~" + x, origen, "     ")))
            print("  Recomendación SUSPENDIDA hasta revisar las reglas.")
        f = frase or decision
        if estado == "CONFLICTO":
            res = (f"recomendación suspendida sobre «{f}» (conflicto en: "
                   f"{', '.join(conflictos)})")
        elif decision in conocidos:
            res = f"{decision}: {f}"
        elif negar(decision) in conocidos:
            res = f"~{decision}: NO {f}"
        else:
            res = f"información insuficiente sobre «{f}»"
        print(f"Decisión ({decision})   : {estado} -> {res}")
    return {"conocidos": conocidos, "estado": estado, "traza": traza,
            "conflictos": conflictos, "usadas": usadas, "nuevas": nuevas,
            "origen": origen}


# ===================================================================
# PROTOCOLO DE DECISIÓN VERIFICABLE: PRÉSTAMO DE EQUIPO DE LABORATORIO
# ===================================================================
VOCABULARIO = {
    "s": "El usuario registró la solicitud de préstamo en el sistema",
    "c": "El usuario completó la capacitación de uso del equipo",
    "m": "El usuario tiene un adeudo (material no devuelto o vencido)",
    "d": "El equipo solicitado está disponible (sin reserva en ese horario)",
    "f": "El equipo aprobó la revisión funcional (batería y encendido)",
    "h": "La solicitud está dentro del horario de préstamo",
    "v": "El usuario está habilitado para recibir préstamos",
    "e": "El equipo es apto para préstamo",
    "x": "Se autoriza el préstamo",
    "n": "Se registra la salida y se notifica al solicitante",
}
DECISION = "x"

REGLAS_ORIGINAL = [
    Regla("R1", "(s & c & ~m) -> v",
          "Si registró solicitud, completó la capacitación y NO tiene adeudo, "
          "el usuario está habilitado"),
    Regla("R2", "(d & f) -> e",
          "Si el equipo está disponible y aprobó la revisión, es apto"),
    Regla("R3", "(v & e & h) -> x",
          "Si el usuario está habilitado, el equipo es apto y es horario de "
          "préstamo, se autoriza"),
    Regla("R4", "x -> n",
          "Si se autoriza, se registra la salida y se notifica"),
    Regla("R5", "m -> ~x",
          "Si el usuario tiene adeudo, no se autoriza"),
    Regla("R6", "~f -> ~e",
          "Si el equipo NO aprobó la revisión, no es apto"),
    Regla("R7", "~d -> ~e",
          "Si el equipo NO está disponible, no es apto para este préstamo"),
    Regla("R8", "~e -> ~x",
          "Si el equipo no es apto, no se autoriza"),
    Regla("R9", "~h -> ~x",
          "Si está fuera del horario, no se autoriza"),
]

# Versión de PRUEBA: R2 se simplifica (error intencional) y omite la revisión.
REGLAS_PRUEBA = [r if r.id != "R2" else
                 Regla("R2", "d -> e",
                       "(PRUEBA) Si el equipo está disponible, es apto")
                 for r in REGLAS_ORIGINAL]

# Versión CORREGIDA: R2 vuelve a exigir la revisión funcional, que es el
# propósito del protocolo (no prestar equipo que no funciona).
REGLAS_CORREGIDA = [r if r.id != "R2" else
                    Regla("R2", "(d & f) -> e",
                          "(CORREGIDA) Solo un equipo disponible Y revisado "
                          "es apto")
                    for r in REGLAS_ORIGINAL]

ESCENARIOS = [
    ("E1", "Caso ideal: todo en orden",
     ["s", "c", "~m", "d", "f", "h"]),
    ("E2", "Usuario con adeudo",
     ["s", "c", "m", "d", "f", "h"]),
    ("E3", "Equipo falla la revisión (batería)",
     ["s", "c", "~m", "d", "~f", "h"]),
    ("E4", "Fuera de horario",
     ["s", "c", "~m", "d", "f", "~h"]),
    ("E5", "Adeudo sin revisar (información insuficiente)",
     ["s", "c", "d", "f", "h"]),
    ("E6", "Equipo ya reservado",
     ["s", "c", "~m", "~d", "f", "h"]),
    ("E7", "Solo datos del usuario, nada del equipo",
     ["s", "c", "~m"]),
    ("E8", "Varias causas de rechazo a la vez",
     ["s", "c", "m", "d", "~f", "~h"]),
]

VERSIONES = {"original": REGLAS_ORIGINAL, "prueba": REGLAS_PRUEBA,
             "corregida": REGLAS_CORREGIDA}


def main():
    import sys
    version = "original"
    elegidos = None
    for arg in sys.argv[1:]:
        if arg in VERSIONES:
            version = arg
        elif arg.upper().startswith("E"):
            elegidos = (elegidos or []) + [arg.upper()]
    reglas = VERSIONES[version]
    print("=" * 70)
    print(f"PROTOCOLO: préstamo de equipo de laboratorio   versión: {version}")
    print("=" * 70)
    print("Vocabulario:")
    for k, v in VOCABULARIO.items():
        print(f"   {k}: {v}")
    print("Reglas:")
    for r in reglas:
        print(f"   {r}    ({r.palabras})")
    for eid, desc, hechos in ESCENARIOS:
        if elegidos and eid not in elegidos:
            continue
        print("-" * 70)
        print(f"{eid}. {desc}")
        ejecutar(hechos, reglas, DECISION, VOCABULARIO[DECISION].lower())


if __name__ == "__main__":
    main()
