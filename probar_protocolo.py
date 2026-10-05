#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
probar_protocolo.py
Ejecuta las pruebas mínimas del taller (Tabla 8) y los ocho escenarios del
protocolo en las versiones original, prueba y corregida.  Para cada escenario
compara el resultado esperado (escrito ANTES de ejecutar) con el obtenido y
comprueba con verificador_consistencia.py la satisfacibilidad conjunta de
hechos y reglas.
Uso: python probar_protocolo.py      (los tres .py deben estar en la misma carpeta)
"""
from tabla_verdad import tabla_verdad
from verificador_consistencia import verificar
import sistema_reglas_proposicional as sr

# Resultado esperado, escrito a mano antes de ejecutar (versión original)
ESPERADO = {
    "E1": "x", "E2": "~x", "E3": "~x", "E4": "~x",
    "E5": "sin conclusión", "E6": "~x", "E7": "sin conclusión", "E8": "~x",
}


def resultado(r):
    if r["estado"] == "CONFLICTO":
        return "conflicto"
    if "x" in r["conocidos"]:
        return "x"
    if "~x" in r["conocidos"]:
        return "~x"
    return "sin conclusión"


def pruebas_minimas():
    print("=" * 70)
    print("PRUEBAS MÍNIMAS DEL TALLER (Tabla 8)")
    print("=" * 70)
    _, clase = tabla_verdad("p | ~p", mostrar=False)
    print(f"1) p | ~p                 -> {clase.split()[0]}")
    ok, mod, _ = verificar(["p", "p -> q"], mostrar=False)
    print(f"2) K = {{p, p->q}}          -> consistente={ok}, modelos={len(mod)}")
    ok, mod, _ = verificar(["p", "p -> q", "~q"], mostrar=False)
    print(f"3) K = {{p, p->q, ~q}}      -> consistente={ok}, modelos={len(mod)}")
    reglas = [sr.Regla("R1", "p -> q"), sr.Regla("R2", "q -> r")]
    r = sr.ejecutar(["p"], reglas, "r", mostrar=False)
    print(f"4) Hecho p; R1, R2        -> conocidos={r['conocidos']}, "
          f"reglas={r['usadas']}")
    print("5) Entradas inválidas:")
    for mala in ["(p & q", "p && q", "p # q", "p -> ", "p q"]:
        try:
            tabla_verdad(mala, mostrar=False)
        except Exception as e:
            print(f"   '{mala}': {e}")


def correr_version(nombre, reglas):
    print("\n" + "=" * 70)
    print(f"ESCENARIOS - versión {nombre.upper()}")
    print("=" * 70)
    filas = []
    for eid, desc, hechos in sr.ESCENARIOS:
        r = sr.ejecutar(hechos, reglas, sr.DECISION, mostrar=False)
        formulas = sr.formulas_de_base(hechos, reglas)
        ok, modelos, _ = verificar(formulas, mostrar=False)
        obt = resultado(r)
        esp = ESPERADO[eid]
        filas.append((eid, desc, ", ".join(hechos), esp, obt,
                      ", ".join(r["usadas"]) or "-",
                      "Sí" if ok else "No", len(modelos),
                      "coincide" if obt == esp else "DIFERENTE"))
    enc = ("Esc", "Hechos", "Esperado", "Obtenido", "Reglas", "Consist.",
           "Modelos", "Comparación")
    print(f"{enc[0]:4}| {enc[1]:24}| {enc[2]:15}| {enc[3]:15}| {enc[4]:22}| "
          f"{enc[5]:8}| {enc[6]:7}| {enc[7]}")
    for f in filas:
        print(f"{f[0]:4}| {f[2]:24}| {f[3]:15}| {f[4]:15}| {f[5]:22}| "
              f"{f[6]:8}| {f[7]:<7}| {f[8]}")
    return filas


if __name__ == "__main__":
    pruebas_minimas()
    resultados = {}
    for nombre, reglas in sr.VERSIONES.items():
        resultados[nombre] = correr_version(nombre, reglas)
