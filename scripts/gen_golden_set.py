#!/usr/bin/env -S uv run --script
# ruff: noqa: E501
# /// script
# dependencies = ["pyyaml"]
# ///
"""Genera el fixture de DEMO de RAT-5: corpus NIIF/NIA de muestra + golden set (≥50 ítems).

⚠️ DATOS DE MUESTRA SINTÉTICOS, revisables por un humano (BR-76) — NO son normas contables
reales auditadas. Sirven para demostrar el loop de Ratchet (recall-por-span + escenario NIIF 16).
Los offsets se calculan por construcción (el span se inserta y se registra su posición exacta),
así que el validador (scripts/validate_golden_set.py) siempre cuadra.

Escenario NIIF 16: seeds/corpus_vigente/ tiene la versión CORRECTA (donde viven los spans);
seeds/corpus/ = mismo corpus salvo niif16, que arranca en su versión VIEJA/derogada (sin los
spans vigentes) → dispara "fuente-vieja". El parche de datos reemplaza niif16 vieja → vigente.

Uso:  uv run --script scripts/gen_golden_set.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"
VIGENTE = SEEDS / "corpus_vigente"
CORPUS = SEEDS / "corpus"

# (id, doc, critical, slice, question, span_text_exacto, answer)
ITEMS: list[tuple[str, str, bool, str, str, str, str]] = [
    # ── NIIF 16 · Arrendamientos (el doc del escenario; varios críticos) ──────
    (
        "niif16-plazo",
        "niif16",
        True,
        "niif16",
        "¿Cómo se determina el plazo del arrendamiento según la NIIF 16?",
        "El plazo del arrendamiento comprende el periodo no cancelable más los periodos cubiertos por una opción de renovación que el arrendatario tenga certeza razonable de ejercer.",
        "El periodo no cancelable más las renovaciones con certeza razonable de ejercicio.",
    ),
    (
        "niif16-activo",
        "niif16",
        True,
        "niif16",
        "¿Qué reconoce el arrendatario al inicio del arrendamiento bajo NIIF 16?",
        "Al comienzo del arrendamiento el arrendatario reconoce un activo por derecho de uso y un pasivo por arrendamiento medido al valor presente de los pagos.",
        "Un activo por derecho de uso y un pasivo por arrendamiento.",
    ),
    (
        "niif16-medicion",
        "niif16",
        False,
        "niif16",
        "¿Cómo se mide inicialmente el pasivo por arrendamiento en la NIIF 16?",
        "El pasivo por arrendamiento se mide inicialmente al valor presente de los pagos por arrendamiento descontados usando la tasa de interés implícita.",
        "Al valor presente de los pagos descontados a la tasa implícita.",
    ),
    (
        "niif16-exencion",
        "niif16",
        False,
        "niif16",
        "¿Qué exenciones de reconocimiento permite la NIIF 16 al arrendatario?",
        "La NIIF 16 permite exenciones de reconocimiento para arrendamientos de corto plazo y para activos de bajo valor, cuyos pagos se reconocen como gasto lineal.",
        "Arrendamientos de corto plazo y activos de bajo valor.",
    ),
    (
        "niif16-corto-plazo",
        "niif16",
        False,
        "niif16",
        "¿Qué es un arrendamiento de corto plazo según la NIIF 16?",
        "Un arrendamiento de corto plazo es aquel cuyo plazo del arrendamiento es de doce meses o menos y que no contiene una opción de compra.",
        "Aquel de doce meses o menos, sin opción de compra.",
    ),
    (
        "niif16-depreciacion",
        "niif16",
        False,
        "niif16",
        "¿Cómo se deprecia el activo por derecho de uso en la NIIF 16?",
        "El activo por derecho de uso se deprecia de forma sistemática a lo largo de la vida útil del activo o del plazo del arrendamiento, el menor de ambos.",
        "Sistemáticamente por el menor entre vida útil y plazo.",
    ),
    (
        "niif16-tasa",
        "niif16",
        True,
        "niif16",
        "¿Qué tasa de descuento usa el arrendatario cuando no puede determinar la tasa implícita?",
        "Cuando la tasa de interés implícita no puede determinarse con facilidad, el arrendatario utiliza su tasa incremental de endeudamiento para descontar los pagos.",
        "Su tasa incremental de endeudamiento.",
    ),
    (
        "niif16-remedicion",
        "niif16",
        False,
        "niif16",
        "¿Cuándo se vuelve a medir el pasivo por arrendamiento bajo NIIF 16?",
        "El arrendatario vuelve a medir el pasivo por arrendamiento cuando cambian los pagos futuros por una modificación del plazo o de la estimación de una opción de compra.",
        "Cuando cambian los pagos por modificación del plazo o de la opción.",
    ),
    # ── NIIF 15 · Ingresos de contratos con clientes ──────────────────────────
    (
        "niif15-modelo",
        "niif15",
        True,
        "niif15",
        "¿Cuál es el modelo de cinco pasos para reconocer ingresos en la NIIF 15?",
        "La NIIF 15 aplica un modelo de cinco pasos: identificar el contrato, identificar las obligaciones de desempeño, determinar el precio de la transacción, asignarlo y reconocer el ingreso al satisfacer cada obligación.",
        "Los cinco pasos del modelo de reconocimiento de ingresos.",
    ),
    (
        "niif15-obligacion",
        "niif15",
        False,
        "niif15",
        "¿Qué es una obligación de desempeño en la NIIF 15?",
        "Una obligación de desempeño es un compromiso en el contrato de transferir al cliente un bien o servicio distinto o una serie de bienes sustancialmente iguales.",
        "El compromiso de transferir un bien o servicio distinto.",
    ),
    (
        "niif15-precio",
        "niif15",
        False,
        "niif15",
        "¿Cómo se determina el precio de la transacción en la NIIF 15?",
        "El precio de la transacción es el importe de la contraprestación que la entidad espera recibir a cambio de transferir los bienes o servicios comprometidos con el cliente.",
        "La contraprestación esperada por transferir los bienes o servicios.",
    ),
    (
        "niif15-momento",
        "niif15",
        True,
        "niif15",
        "¿Cuándo reconoce ingresos una entidad bajo la NIIF 15?",
        "La entidad reconoce el ingreso cuando satisface una obligación de desempeño transfiriendo el control del bien o servicio al cliente, en un momento o a lo largo del tiempo.",
        "Cuando transfiere el control, en un momento o a lo largo del tiempo.",
    ),
    (
        "niif15-variable",
        "niif15",
        False,
        "niif15",
        "¿Cómo se trata la contraprestación variable en la NIIF 15?",
        "La contraprestación variable se estima usando el valor esperado o el importe más probable, limitada para que sea altamente probable que no ocurra una reversión significativa.",
        "Se estima con valor esperado o importe más probable, con límite de reversión.",
    ),
    (
        "niif15-costos",
        "niif15",
        False,
        "niif15",
        "¿Qué costos incrementales del contrato se capitalizan en la NIIF 15?",
        "Los costos incrementales de obtener un contrato se reconocen como activo si la entidad espera recuperarlos a lo largo de la relación con el cliente.",
        "Los costos incrementales recuperables de obtener el contrato.",
    ),
    (
        "niif15-garantia",
        "niif15",
        False,
        "niif15",
        "¿Cómo se contabiliza una garantía como obligación de desempeño en la NIIF 15?",
        "Cuando el cliente puede contratar la garantía por separado, esta constituye una obligación de desempeño distinta a la que se asigna parte del precio de la transacción.",
        "Como obligación de desempeño distinta si es contratable por separado.",
    ),
    # ── NIIF 9 · Instrumentos financieros ─────────────────────────────────────
    (
        "niif9-clasificacion",
        "niif9",
        True,
        "niif9",
        "¿Cómo se clasifican los activos financieros según la NIIF 9?",
        "La NIIF 9 clasifica los activos financieros según el modelo de negocio de la entidad y las características de los flujos de efectivo contractuales del instrumento.",
        "Por el modelo de negocio y las características de los flujos contractuales.",
    ),
    (
        "niif9-deterioro",
        "niif9",
        True,
        "niif9",
        "¿Qué modelo de deterioro introduce la NIIF 9?",
        "La NIIF 9 introduce un modelo de pérdidas crediticias esperadas que exige reconocer el deterioro antes de que ocurra un evento de incumplimiento.",
        "El modelo de pérdidas crediticias esperadas.",
    ),
    (
        "niif9-costo-amortizado",
        "niif9",
        False,
        "niif9",
        "¿Cuándo se mide un activo financiero al costo amortizado en la NIIF 9?",
        "Un activo financiero se mide al costo amortizado cuando se mantiene para cobrar flujos contractuales que son únicamente pagos de principal e intereses.",
        "Cuando se mantiene para cobrar principal e intereses.",
    ),
    (
        "niif9-cobertura",
        "niif9",
        False,
        "niif9",
        "¿Qué relación de cobertura reconoce la contabilidad de coberturas de la NIIF 9?",
        "La contabilidad de coberturas de la NIIF 9 reconoce una relación económica entre el instrumento de cobertura y la partida cubierta que compensa cambios de valor.",
        "Una relación económica de compensación entre instrumento y partida cubierta.",
    ),
    (
        "niif9-baja",
        "niif9",
        False,
        "niif9",
        "¿Cuándo se da de baja un activo financiero según la NIIF 9?",
        "Un activo financiero se da de baja cuando expiran los derechos contractuales sobre los flujos de efectivo o cuando se transfieren sustancialmente los riesgos y beneficios.",
        "Cuando expiran los derechos o se transfieren riesgos y beneficios.",
    ),
    (
        "niif9-valor-razonable",
        "niif9",
        False,
        "niif9",
        "¿Qué activos se miden a valor razonable con cambios en resultados en la NIIF 9?",
        "Se miden a valor razonable con cambios en resultados los activos financieros mantenidos para negociar y aquellos que no cumplen el criterio de flujos contractuales.",
        "Los mantenidos para negociar y los que no cumplen el criterio de flujos.",
    ),
    # ── NIIF 13 · Medición del valor razonable ────────────────────────────────
    (
        "niif13-definicion",
        "niif13",
        False,
        "niif13",
        "¿Cómo define la NIIF 13 el valor razonable?",
        "La NIIF 13 define el valor razonable como el precio que se recibiría por vender un activo o se pagaría por transferir un pasivo en una transacción ordenada entre participantes del mercado.",
        "El precio de venta o transferencia en una transacción ordenada de mercado.",
    ),
    (
        "niif13-jerarquia",
        "niif13",
        True,
        "niif13",
        "¿Qué niveles tiene la jerarquía del valor razonable en la NIIF 13?",
        "La jerarquía del valor razonable de la NIIF 13 tiene tres niveles según las variables usadas: precios cotizados, datos observables y datos no observables.",
        "Tres niveles: precios cotizados, datos observables y no observables.",
    ),
    (
        "niif13-mercado",
        "niif13",
        False,
        "niif13",
        "¿Qué mercado usa la NIIF 13 para medir el valor razonable?",
        "La medición del valor razonable supone que la transacción ocurre en el mercado principal del activo o pasivo o, en su ausencia, en el mercado más ventajoso.",
        "El mercado principal o, en su ausencia, el más ventajoso.",
    ),
    (
        "niif13-tecnicas",
        "niif13",
        False,
        "niif13",
        "¿Qué técnicas de valoración reconoce la NIIF 13?",
        "La NIIF 13 reconoce técnicas de valoración de enfoque de mercado, de costo y de ingreso, que deben maximizar el uso de variables observables.",
        "Enfoques de mercado, costo e ingreso, maximizando variables observables.",
    ),
    # ── NIA 315 · Identificación de riesgos ───────────────────────────────────
    (
        "nia315-riesgo-inherente",
        "nia315",
        False,
        "nia",
        "¿Qué es el riesgo inherente según la NIA 315?",
        "El riesgo inherente es la susceptibilidad de una afirmación a una incorrección que pudiera ser material, antes de considerar los controles relacionados.",
        "La susceptibilidad de una afirmación a incorrección material antes de controles.",
    ),
    (
        "nia315-comprension",
        "nia315",
        True,
        "nia",
        "¿Qué debe comprender el auditor según la NIA 315?",
        "La NIA 315 exige que el auditor obtenga una comprensión de la entidad y su entorno, incluido su control interno, para identificar y valorar los riesgos de incorrección material.",
        "La entidad, su entorno y su control interno para valorar los riesgos.",
    ),
    (
        "nia315-controles",
        "nia315",
        False,
        "nia",
        "¿Qué componentes del control interno considera la NIA 315?",
        "La NIA 315 considera componentes del control interno como el entorno de control, el proceso de valoración de riesgos, las actividades de control y el seguimiento.",
        "Entorno de control, valoración de riesgos, actividades de control y seguimiento.",
    ),
    (
        "nia315-significativo",
        "nia315",
        True,
        "nia",
        "¿Qué es un riesgo significativo en la NIA 315?",
        "Un riesgo significativo es un riesgo identificado y valorado de incorrección material que, a juicio del auditor, requiere una consideración especial de auditoría.",
        "Un riesgo valorado que requiere consideración especial de auditoría.",
    ),
    (
        "nia315-procedimientos",
        "nia315",
        False,
        "nia",
        "¿Qué procedimientos de valoración del riesgo aplica el auditor en la NIA 315?",
        "El auditor aplica procedimientos de valoración del riesgo que incluyen indagaciones, procedimientos analíticos y observación e inspección para sustentar su comprensión.",
        "Indagaciones, procedimientos analíticos y observación e inspección.",
    ),
    # ── NIA 330 · Respuestas del auditor a los riesgos valorados ──────────────
    (
        "nia330-respuestas",
        "nia330",
        True,
        "nia",
        "¿Qué respuestas globales exige la NIA 330 frente a los riesgos valorados?",
        "La NIA 330 exige que el auditor diseñe e implemente respuestas globales para responder a los riesgos valorados de incorrección material en los estados financieros.",
        "Diseñar respuestas globales a los riesgos valorados en los estados financieros.",
    ),
    (
        "nia330-sustantivos",
        "nia330",
        False,
        "nia",
        "¿Qué procedimientos sustantivos requiere la NIA 330?",
        "La NIA 330 requiere que el auditor diseñe y ejecute procedimientos sustantivos para cada tipo de transacción, saldo contable y revelación que sea material.",
        "Procedimientos sustantivos para cada transacción, saldo y revelación material.",
    ),
    (
        "nia330-controles",
        "nia330",
        False,
        "nia",
        "¿Cuándo prueba el auditor la eficacia operativa de los controles según la NIA 330?",
        "El auditor prueba la eficacia operativa de los controles cuando su valoración del riesgo espera que los controles operen con eficacia o cuando los procedimientos sustantivos no bastan.",
        "Cuando espera que los controles operen con eficacia o lo sustantivo no basta.",
    ),
    (
        "nia330-suficiencia",
        "nia330",
        True,
        "nia",
        "¿Qué evalúa el auditor sobre la evidencia según la NIA 330?",
        "La NIA 330 exige que el auditor evalúe si la evidencia de auditoría obtenida es suficiente y adecuada para reducir el riesgo de auditoría a un nivel aceptablemente bajo.",
        "Si la evidencia es suficiente y adecuada para reducir el riesgo de auditoría.",
    ),
    # ── NIIF 7 · Revelaciones de instrumentos financieros ─────────────────────
    (
        "niif7-riesgos",
        "niif7",
        False,
        "niif7",
        "¿Qué riesgos exige revelar la NIIF 7 sobre instrumentos financieros?",
        "La NIIF 7 exige revelar la naturaleza y el alcance de los riesgos de crédito, de liquidez y de mercado que surgen de los instrumentos financieros.",
        "Riesgos de crédito, de liquidez y de mercado.",
    ),
    (
        "niif7-liquidez",
        "niif7",
        False,
        "niif7",
        "¿Qué revela una entidad sobre el riesgo de liquidez según la NIIF 7?",
        "Sobre el riesgo de liquidez la NIIF 7 exige revelar un análisis de vencimientos de los pasivos financieros que muestre los flujos contractuales remanentes.",
        "Un análisis de vencimientos de los pasivos financieros.",
    ),
    (
        "niif7-credito",
        "niif7",
        True,
        "niif7",
        "¿Qué información sobre riesgo de crédito exige la NIIF 7?",
        "La NIIF 7 exige revelar información sobre la exposición máxima al riesgo de crédito, las garantías tomadas y la calidad crediticia de los activos financieros.",
        "Exposición máxima, garantías y calidad crediticia.",
    ),
    (
        "niif7-mercado",
        "niif7",
        False,
        "niif7",
        "¿Qué análisis de sensibilidad requiere la NIIF 7 para el riesgo de mercado?",
        "La NIIF 7 requiere un análisis de sensibilidad que muestre cómo el resultado y el patrimonio se verían afectados por cambios razonablemente posibles en las variables de mercado.",
        "Un análisis de sensibilidad ante cambios razonables en variables de mercado.",
    ),
    # ── NIC 36 · Deterioro del valor de los activos ───────────────────────────
    (
        "nic36-indicios",
        "nic36",
        False,
        "nic",
        "¿Cuándo evalúa una entidad el deterioro de un activo según la NIC 36?",
        "La NIC 36 exige evaluar en cada cierre si existen indicios de deterioro y, de existir, estimar el importe recuperable del activo.",
        "En cada cierre, si hay indicios, estimando el importe recuperable.",
    ),
    (
        "nic36-recuperable",
        "nic36",
        True,
        "nic",
        "¿Cómo se determina el importe recuperable en la NIC 36?",
        "El importe recuperable es el mayor entre el valor razonable menos los costos de disposición y el valor en uso del activo o de la unidad generadora de efectivo.",
        "El mayor entre valor razonable menos costos y valor en uso.",
    ),
    (
        "nic36-uge",
        "nic36",
        False,
        "nic",
        "¿Qué es una unidad generadora de efectivo en la NIC 36?",
        "Una unidad generadora de efectivo es el grupo identificable más pequeño de activos que genera entradas de efectivo independientes de otros activos.",
        "El grupo más pequeño de activos que genera efectivo independiente.",
    ),
    (
        "nic36-reversion",
        "nic36",
        False,
        "nic",
        "¿Cuándo se revierte una pérdida por deterioro según la NIC 36?",
        "La pérdida por deterioro se revierte cuando cambian las estimaciones usadas para determinar el importe recuperable, salvo para la plusvalía que nunca se revierte.",
        "Cuando cambian las estimaciones, salvo la plusvalía.",
    ),
    # ── NIC 37 · Provisiones ──────────────────────────────────────────────────
    (
        "nic37-provision",
        "nic37",
        True,
        "nic",
        "¿Cuándo se reconoce una provisión según la NIC 37?",
        "La NIC 37 exige reconocer una provisión cuando existe una obligación presente resultado de un suceso pasado, es probable una salida de recursos y puede estimarse con fiabilidad.",
        "Obligación presente por suceso pasado, salida probable y estimación fiable.",
    ),
    (
        "nic37-contingente",
        "nic37",
        False,
        "nic",
        "¿Qué es un pasivo contingente en la NIC 37?",
        "Un pasivo contingente es una obligación posible surgida de sucesos pasados cuya existencia se confirmará por eventos futuros inciertos no enteramente bajo control de la entidad.",
        "Una obligación posible confirmada por eventos futuros inciertos.",
    ),
    (
        "nic37-onerosos",
        "nic37",
        False,
        "nic",
        "¿Cómo trata la NIC 37 los contratos de carácter oneroso?",
        "La NIC 37 exige reconocer y medir como provisión la obligación presente derivada de un contrato oneroso cuyos costos inevitables superan los beneficios esperados.",
        "Se provisiona la obligación del contrato oneroso.",
    ),
    (
        "nic37-reembolso",
        "nic37",
        False,
        "nic",
        "¿Cómo se reconoce un reembolso esperado de una provisión en la NIC 37?",
        "Cuando se espera un reembolso de un tercero, la NIC 37 lo reconoce como un activo separado solo si es prácticamente seguro que se recibirá al liquidar la obligación.",
        "Como activo separado solo si es prácticamente seguro.",
    ),
    # ── NIC 2 · Inventarios ───────────────────────────────────────────────────
    (
        "nic2-medicion",
        "nic2",
        False,
        "nic",
        "¿Cómo se miden los inventarios según la NIC 2?",
        "La NIC 2 exige medir los inventarios al menor entre el costo y el valor neto realizable.",
        "Al menor entre costo y valor neto realizable.",
    ),
    (
        "nic2-costo",
        "nic2",
        False,
        "nic",
        "¿Qué incluye el costo de los inventarios en la NIC 2?",
        "El costo de los inventarios comprende los costos de adquisición, los costos de transformación y otros costos incurridos para darles su condición y ubicación actuales.",
        "Adquisición, transformación y otros costos para su condición actual.",
    ),
    (
        "nic2-formulas",
        "nic2",
        False,
        "nic",
        "¿Qué fórmulas de costo permite la NIC 2?",
        "La NIC 2 permite las fórmulas de costo de identificación específica, primeras entradas primeras salidas y costo promedio ponderado.",
        "Identificación específica, PEPS y promedio ponderado.",
    ),
    (
        "nic2-vnr",
        "nic2",
        True,
        "nic",
        "¿Qué es el valor neto realizable en la NIC 2?",
        "El valor neto realizable es el precio estimado de venta en el curso normal de la operación menos los costos estimados de terminación y de venta.",
        "Precio de venta estimado menos costos de terminación y venta.",
    ),
    # (52 ítems)
]

FILLER = (
    "\n\nEsta sección del documento de muestra desarrolla el requerimiento con contexto "
    "adicional para efectos de recuperación por span. El texto que sigue es la afirmación dorada:\n\n"
)


def build() -> None:
    VIGENTE.mkdir(parents=True, exist_ok=True)
    CORPUS.mkdir(parents=True, exist_ok=True)

    by_doc: dict[str, list] = {}
    for it in ITEMS:
        by_doc.setdefault(it[1], []).append(it)

    gs_items = []
    for doc_id, items in by_doc.items():
        parts = [f"# {doc_id.upper()} — documento de muestra (sintético, DEMO)\n"]
        pos = len(parts[0])
        for iid, _doc, critical, slc, q, span, ans in items:
            header = f"{FILLER}## {iid}\n\n"
            parts.append(header)
            pos += len(header)
            start = pos
            parts.append(span)
            pos += len(span)
            end = pos
            gs_items.append(
                {
                    "item_id": iid,
                    "question": q,
                    "answer": ans,
                    "gold_span": {"doc_id": doc_id, "start": start, "end": end, "text": span},
                    "critical": critical,
                    "slice": slc,
                }
            )
        (VIGENTE / f"{doc_id}.txt").write_text("".join(parts), encoding="utf-8")

    # corpus/ (estado inicial) = copia de vigente, SALVO niif16 (versión vieja/derogada)
    for f in VIGENTE.glob("*.txt"):
        shutil.copy(f, CORPUS / f.name)
    (CORPUS / "niif16.txt").write_text(
        "# NIIF16 — VERSIÓN VIEJA / DEROGADA (documento de muestra, DEMO)\n\n"
        "Esta es la versión antigua de la norma de arrendamientos que el corpus está citando.\n"
        "El modelo de arrendamiento operativo bajo la norma derogada NIC 17 no reconocía un activo\n"
        "por derecho de uso ni un pasivo por arrendamiento en el estado de situación financiera.\n"
        "Ninguna de las afirmaciones vigentes de la NIIF 16 aparece aquí → dispara 'fuente-vieja'.\n",
        encoding="utf-8",
    )

    (SEEDS / "golden_set_niif.yaml").write_text(
        "# Golden Set — Camino NIIF (U1) · RAT-5 · DATOS DE MUESTRA SINTÉTICOS (revisar — BR-76)\n"
        "# Generado por scripts/gen_golden_set.py (offsets exactos por construcción).\n"
        "# NO son normas reales auditadas; sirven para demostrar el loop de Ratchet.\n\n"
        + yaml.safe_dump({"version": 1, "items": gs_items}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    n_crit = sum(1 for it in ITEMS if it[2])
    n_niif16 = sum(1 for it in ITEMS if it[3] == "niif16")
    print(
        f"Generado: {len(ITEMS)} ítems · {n_crit} críticos · {n_niif16} NIIF16 · {len(by_doc)} docs"
    )


if __name__ == "__main__":
    build()
