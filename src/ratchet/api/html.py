"""Render del `Report` a HTML self-contained — identidad corporativa Caseware.

Sin assets externos (CSS inline, fuentes del sistema): abrible en navegador, sin red. Azul índigo
+ coral + crema, tema claro. Todo campo de usuario pasa por `escape()` (anti-XSS).
"""
# ruff: noqa: E501 -- plantilla HTML/CSS: las líneas largas son contenido, no lógica.

from __future__ import annotations

from html import escape

from ratchet.domain import Capa, GateDecision, Report, ReportDecision, RunRecord

# Decisión → (etiqueta legible, token de estado). No es color-solo (label + ícono).
_DECISION: dict[ReportDecision, tuple[str, str]] = {
    ReportDecision.DEPLOY: ("▲ Deploy aprobado", "ok"),
    ReportDecision.REVERT: ("⟲ Revertido a lo seguro", "bad"),
    ReportDecision.PENDING: ("◴ Pendiente de aprobación", "warn"),
    ReportDecision.INCONCLUSA: ("⃠ Inconclusa", "mut"),
    ReportDecision.SIN_CAMBIO: ("= Sin cambio", "mut"),
    ReportDecision.DETENIDA: ("✋ Detenida por humano", "warn"),
}

# Capa localizada → nodo del lineage que se marca como defectuoso.
_BAD_NODE: dict[Capa, str] = {
    Capa.FUENTE_VIEJA: "documento",
    Capa.COBERTURA: "documento",
    Capa.CHUNKING: "chunk",
    Capa.RETRIEVAL_MISS: "retrieve",
    Capa.GENERACION: "genera",
}

_STAGES = [
    ("Monitoreando", "signal"),
    ("Investigando", "diagnosis"),
    ("Aplicando parche", "patch"),
    ("Gate", "verdict"),
    ("Reporte", None),
]


def _num(v: float | None) -> str:
    return f"{v:.2f}" if v is not None else "—"


def _signed(v: float | None) -> str:
    return f"{v:+.2f}" if v is not None else "—"


def _pct(v: float | None) -> str:
    return f"{max(0.0, min(1.0, v)) * 100:.0f}%" if v is not None else "0%"


def render_report_html(report: Report, run: RunRecord) -> str:
    label, tok = _DECISION.get(report.decision, (report.decision.value, "mut"))
    capa = run.diagnosis.capa if run.diagnosis is not None else None
    capa_txt = capa.value if capa is not None else "—"
    fix_txt = run.diagnosis.fix_layer.value if run.diagnosis is not None else "—"
    evidencia = escape(" · ".join(run.diagnosis.evidencia)) if run.diagnosis is not None else "—"
    change = escape(report.change or "—")
    bad = _BAD_NODE.get(capa, "") if capa is not None else ""

    nodes = ""
    for name, node_id in [
        ("Documento", "documento"),
        ("Chunk", "chunk"),
        ("Retrieve", "retrieve"),
        ("Genera", "genera"),
    ]:
        cls = "node bad" if node_id == bad else "node"
        st = "Fuente vieja" if node_id == bad else "OK"
        sep = '<div class="arr">→</div>' if node_id != "genera" else ""
        nodes += f'<div class="{cls}">{name}<span class="st">{escape(st)}</span></div>{sep}'

    steps = "".join(
        f'<span class="step {"done" if (field is None or getattr(run, field) is not None) else "todo"}">{escape(name)}</span>'
        for name, field in _STAGES
    )

    gate = ""
    if run.verdict is not None:
        v = run.verdict
        cls = "ok" if v.decision is GateDecision.APPROVE else "bad"
        verb = "Aprobado" if v.decision is GateDecision.APPROVE else "Revertido"
        gate = f"""
      <div class="sec">
        <div class="eyebrow">Gate de no-regresión · determinista</div>
        <div class="kv">
          <span class="pill {cls}">{"✓" if cls == "ok" else "⟲"} {escape(verb)}</span>
          <span class="mono">CI [ {_signed(v.ci_delta[0])} · {_signed(v.ci_delta[1])} ]</span>
          <span class="mono">🔒 {v.regressions_criticas} regresiones críticas</span>
          <span class="dim">criterio · {escape(v.criterio)}</span>
        </div>
      </div>"""

    key = "—"
    if report.reproducible_from is not None:
        r = report.reproducible_from
        key = escape(
            f"gs:{r.golden_set_version} · cfg:{r.config_hash[:8]} · corpus:{r.corpus_hash[:8]} · k={r.k} · τ={r.tau}"
        )

    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ratchet · incidente {escape(report.run_id)}</title>
<style>{_CSS}</style></head>
<body>
<div class="page"><div class="shell">
  <div class="hero">
    <div class="nav"><span class="mk">◆</span>Ratchet<small>· knowledge on-call</small></div>
    <div class="badge {tok}">{escape(label)}</div>
    <h1>Reporte de incidente</h1>
    <p>Confiabilidad del asistente NIIF — localizada y corregida en la capa correcta, sin red y sin invocar el LLM.</p>
  </div>
  <div class="card">
    <div class="sec">
      <div class="eyebrow">Recall · antes <span class="co">/</span> después</div>
      <div class="mrow"><span class="t">Antes</span><span class="n">{_num(report.recall_before)}</span>
        <div class="bar"><i class="b" style="width:{_pct(report.recall_before)}"></i></div></div>
      <div class="mrow"><span class="t">Después</span><span class="n">{_num(report.recall_after)}</span>
        <div class="bar"><i class="a" style="width:{_pct(report.recall_after)}"></i></div></div>
      <div class="recover"><span class="d">{_signed(report.delta)}</span>
        <span>Recuperación · el gate valida las regresiones en clase crítica</span></div>
    </div>
    <div class="sec">
      <div class="eyebrow">Lineage · dónde estaba el defecto</div>
      <div class="flow">{nodes}</div>
      <div class="pin">◆ Capa <b>{escape(capa_txt)}</b> → fix en <b>{escape(fix_txt)}</b></div>
    </div>{gate}
    <div class="sec">
      <div class="eyebrow">Trazabilidad · máquina de estados</div>
      <div class="steps">{steps}</div>
    </div>
    <div class="sec">
      <div class="eyebrow">Diagnóstico · read-only (G3)</div>
      <div class="kv"><span class="mono ink">{escape(capa_txt)} → {escape(fix_txt)}</span>
        <span class="dim">evidencia · {evidencia}</span></div>
      <div class="fix">{change}</div>
    </div>
  </div>
  <div class="foot">
    <span>Reproducible desde <code>{key}</code></span>
    <span>El razonamiento propone · la matemática dispone</span>
  </div>
</div></div>
</body></html>
"""


_CSS = """
:root{
  --indigo:oklch(0.47 0.20 273);--blue:oklch(0.56 0.20 264);--indigo-deep:oklch(0.37 0.16 276);
  --cream:oklch(0.965 0.008 85);--card:#fff;--ink:oklch(0.24 0.035 276);
  --muted:oklch(0.52 0.03 276);--faint:oklch(0.70 0.02 276);--line:oklch(0.90 0.012 276);--line2:oklch(0.94 0.008 276);
  --coral:oklch(0.68 0.17 12);--coral-soft:oklch(0.94 0.05 20);--green:oklch(0.64 0.14 158);--green-soft:oklch(0.95 0.05 158);
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --mono:ui-monospace,"SF Mono","JetBrains Mono",Menlo,monospace;
}
*{box-sizing:border-box}
body{margin:0;background:var(--cream);color:var(--ink);font:15px/1.6 var(--sans)}
.page{min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:0 18px 56px}
.shell{width:min(820px,100%)}
.hero{margin-top:34px;border-radius:26px 26px 0 0;padding:34px 40px 40px;color:#fff;position:relative;overflow:hidden;
  background:radial-gradient(circle at 1.4px 1.4px,rgba(255,255,255,.16) 1.4px,transparent 0) 0 0/22px 22px,linear-gradient(125deg,var(--blue),var(--indigo) 55%,var(--indigo-deep))}
.nav{display:flex;align-items:center;gap:11px;font-weight:700;font-size:15px}
.nav .mk{width:26px;height:26px;border-radius:8px;display:grid;place-items:center;font-size:14px;background:linear-gradient(135deg,var(--coral),oklch(0.62 0.19 320));box-shadow:0 6px 16px -6px oklch(0.5 0.2 340/.8)}
.nav small{font-weight:400;opacity:.72}
.hero h1{margin:26px 0 8px;font-size:33px;line-height:1.1;font-weight:800;letter-spacing:-.02em;text-wrap:balance}
.hero p{margin:0;max-width:54ch;opacity:.86}
.badge{position:absolute;top:34px;right:40px;display:inline-flex;align-items:center;gap:7px;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.34);padding:9px 16px;border-radius:999px;font-weight:700;font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-top:none;border-radius:0 0 26px 26px;padding:8px 40px 30px;box-shadow:0 34px 70px -40px oklch(0.4 0.1 276/.5)}
.sec{padding:24px 0;border-top:1px solid var(--line2)}
.sec:first-child{border-top:none}
.eyebrow{font-size:11.5px;font-weight:700;letter-spacing:.13em;text-transform:uppercase;color:var(--indigo);margin-bottom:15px}
.eyebrow .co{color:var(--coral)}
.mrow{display:grid;grid-template-columns:76px 60px 1fr;align-items:center;gap:16px;margin:12px 0}
.mrow .t{color:var(--muted);font-size:14px;font-weight:600}
.mrow .n{font-size:19px;font-weight:800;font-variant-numeric:tabular-nums}
.bar{height:14px;border-radius:8px;background:var(--line2);overflow:hidden;border:1px solid var(--line)}
.bar i{display:block;height:100%;border-radius:8px}
.bar .b{background:linear-gradient(90deg,oklch(0.74 0.15 20),var(--coral))}
.bar .a{background:linear-gradient(90deg,oklch(0.72 0.13 160),var(--green))}
.recover{margin-top:18px;display:flex;align-items:center;gap:14px;background:var(--green-soft);border:1px solid oklch(0.85 0.09 158);border-radius:14px;padding:14px 20px}
.recover .d{font-size:29px;font-weight:800;color:var(--green);letter-spacing:-.02em}
.recover span{color:oklch(0.42 0.08 158);font-weight:600;font-size:14px}
.flow{display:flex;align-items:stretch;flex-wrap:wrap}
.node{flex:1;min-width:104px;text-align:center;padding:15px 10px;border:1.5px solid var(--line);border-radius:14px;background:var(--card);font-weight:700;font-size:14px}
.node .st{display:block;font-weight:600;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint);margin-top:5px}
.node.bad{border-color:var(--coral);background:var(--coral-soft)}
.node.bad .st{color:var(--coral)}
.arr{display:flex;align-items:center;color:var(--faint);padding:0 8px;font-size:16px}
.pin{margin-top:15px;color:oklch(0.5 0.14 15);font-size:14px}
.pin b{color:var(--ink)}
.kv{display:flex;flex-wrap:wrap;align-items:center;gap:13px;font-size:14px}
.pill{display:inline-flex;align-items:center;gap:7px;padding:7px 15px;border-radius:999px;font-weight:700;font-size:13px}
.pill.ok{background:var(--green-soft);color:oklch(0.45 0.11 158);border:1px solid oklch(0.85 0.09 158)}
.pill.bad{background:var(--coral-soft);color:oklch(0.5 0.15 15);border:1px solid oklch(0.85 0.1 15)}
.mono{font-family:var(--mono);color:var(--muted);font-size:13px}.mono.ink{color:var(--ink);font-weight:700}
.dim{color:var(--muted)}
.steps{display:flex;flex-wrap:wrap;gap:9px}
.step{font-size:12.5px;font-weight:600;padding:7px 14px;border-radius:10px;position:relative;background:oklch(0.96 0.02 273);color:var(--indigo);border:1px solid oklch(0.90 0.03 273)}
.step:not(:last-child)::after{content:"→";position:absolute;right:-13px;top:50%;transform:translateY(-50%);color:var(--faint);font-size:12px}
.step.done{background:var(--indigo);color:#fff;border-color:var(--indigo)}
.step.todo{opacity:.5}
.fix{margin-top:12px;background:var(--cream);border-left:3px solid var(--coral);border-radius:0 12px 12px 0;padding:14px 18px;color:var(--muted);font-size:14px}
.foot{width:100%;margin-top:16px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;color:var(--muted);font-size:12.5px;padding:0 6px}
.foot code{font-family:var(--mono);color:var(--indigo);background:oklch(0.96 0.02 273);padding:2px 8px;border-radius:6px}
"""
