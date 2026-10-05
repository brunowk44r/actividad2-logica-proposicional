#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tabla_verdad.py
Recibe una fórmula escrita con letras y conectivos, identifica sus variables,
genera todas las valuaciones (N = 2^n), muestra columnas intermedias y la
clasifica como tautología, contradicción o contingencia.

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


AYUDA = """
Uso:  python tabla_verdad.py "((p & q) -> r)"
      python tabla_verdad.py            (modo interactivo; escriba 'salir')
Escritura:  ~ negación   & conjunción   | disyunción   -> implicación
            <-> bicondicional   ( ) agrupación   letras minúsculas = variables
Ejemplo:    ((p & q) -> r)      ~(p & q) <-> (~p | ~q)
"""


def clasificar(columna):
    if all(columna):
        return "TAUTOLOGÍA (verdadera en todas las valuaciones)"
    if not any(columna):
        return "CONTRADICCIÓN (falsa en todas las valuaciones)"
    return "CONTINGENCIA (verdadera en algunas valuaciones y falsa en otras)"


def tabla_verdad(texto, mostrar=True):
    """Genera la tabla completa de la fórmula y devuelve (filas, clase)."""
    arbol = leer_formula(texto)
    letras = sorted(variables(arbol))
    columnas = subformulas(arbol)            # intermedias + final
    encabezados = letras + [a_texto(c) for c in columnas]
    anchos = [max(3, len(h)) for h in encabezados]
    filas, final = [], []
    for val in valuaciones(letras):
        fila = [vf(val[x]) for x in letras]
        fila += [vf(evaluar(c, val)) for c in columnas]
        filas.append(fila)
        final.append(evaluar(arbol, val))
    clase = clasificar(final)
    if mostrar:
        print(f"\nFórmula: {a_texto(arbol)}")
        print(f"Variables: {', '.join(letras)}  ->  N = 2^{len(letras)} = "
              f"{2 ** len(letras)} filas\n")
        print(" | ".join(h.center(w) for h, w in zip(encabezados, anchos)))
        print("-+-".join("-" * w for w in anchos))
        for f in filas:
            print(" | ".join(v.center(w) for v, w in zip(f, anchos)))
        print(f"\nColumna final: {', '.join(vf(b) for b in final)}")
        print(f"Clasificación: {clase}")
        print(f"Filas verdaderas: {sum(final)} de {len(final)}")
    return filas, clase


def main():
    import sys
    if len(sys.argv) > 1:
        entradas = [" ".join(sys.argv[1:])]
    else:
        print(AYUDA)
        entradas = None
    while True:
        if entradas is not None:
            if not entradas:
                break
            texto = entradas.pop(0)
        else:
            try:
                texto = input("Fórmula> ").strip()
            except EOFError:
                break
            if texto.lower() in ("salir", "exit", "q"):
                break
            if texto.lower() in ("ayuda", "help", "?", ""):
                print(AYUDA)
                continue
        try:
            tabla_verdad(texto)
        except ErrorFormula as e:
            print(f"Error en la fórmula: {e}")


if __name__ == "__main__":
    main()
