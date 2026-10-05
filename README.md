# Actividad 2 · Protocolo de decisión verificable

**Lógica proposicional como lenguaje formal para decisiones consistentes**
Caso: préstamo de equipo de laboratorio

- **Asignatura:** Fundamentos de Inteligencia Artificial (E-FIA-3), Universidad Politécnica de Pachuca
- **Estudiante:** Bruno Huerta Morales
- **Docente:** Dr. Jaime Aguilar Ortiz
- **Periodo:** septiembre–diciembre de 2026

## Archivos

| Archivo | Función |
|---|---|
| `tabla_verdad.py` | Lee una fórmula, genera las 2^n valuaciones con columnas intermedias y la clasifica (tautología, contradicción, contingencia). |
| `verificador_consistencia.py` | Evalúa varias fórmulas en las mismas valuaciones; informa cuántos modelos hay o declara «base inconsistente». |
| `sistema_reglas_proposicional.py` | Encadenamiento hacia adelante con traza; detecta conflictos y reporta «conclusión obtenida», «sin conclusión» o «conflicto». Incluye el protocolo (10 proposiciones, 9 reglas, 8 escenarios) en las versiones original, prueba y corregida. |
| `probar_protocolo.py` | Pruebas mínimas del taller y tabla de los 8 escenarios en las tres versiones, con verificación de consistencia. |
| `LEEME.txt` | Instrucciones de ejecución. |

Los tres programas incluyen el mismo lector de fórmulas (sin `eval`) para que cada uno funcione por separado.
Escritura: `~` negación, `&` conjunción, `|` disyunción, `->` implicación, `<->` bicondicional.

## Ejecución

Requiere Python 3.8 o superior. No se usan paquetes adicionales. En Spyder: abrir el archivo y pulsar F5.

```bash
python tabla_verdad.py "((p & q) -> r)"
python verificador_consistencia.py "p" "(p -> q)" "~q"
python sistema_reglas_proposicional.py            # versión original, 8 escenarios
python sistema_reglas_proposicional.py prueba E3  # inconsistencia intencional
python sistema_reglas_proposicional.py corregida
python probar_protocolo.py                        # todas las pruebas
```

## Protocolo

| Regla | Fórmula | En palabras |
|---|---|---|
| R1 | (s ∧ c ∧ ¬m) → v | Solicitud registrada, capacitación completada y sin adeudo: usuario habilitado |
| R2 | (d ∧ f) → e | Equipo disponible y con revisión aprobada: equipo apto |
| R3 | (v ∧ e ∧ h) → x | Usuario habilitado, equipo apto y en horario: se autoriza |
| R4 | x → n | Si se autoriza, se registra y notifica |
| R5 | m → ¬x | Con adeudo no se autoriza |
| R6 | ¬f → ¬e | Revisión fallida: equipo no apto |
| R7 | ¬d → ¬e | Equipo no disponible: no apto |
| R8 | ¬e → ¬x | Equipo no apto: no se autoriza |
| R9 | ¬h → ¬x | Fuera de horario: no se autoriza |

La versión de prueba cambia R2 por `d → e`, lo que produce un conflicto en E3 y E8. La corrección restablece `(d ∧ f) → e`.
