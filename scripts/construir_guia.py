#!/usr/bin/env python3
"""Genera las gráficas, la guía PDF y el README del caso de cartera."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from weasyprint import HTML

BASE = Path("/home/rimas/cartera-clientes")
DATOS = BASE / "datos"
CAPTURAS = BASE / "capturas"
CAPTURAS.mkdir(parents=True, exist_ok=True)
R = json.loads((DATOS / "resumen.json").read_text(encoding="utf-8"))

NAVY = "#16324F"
TEAL = "#2A7F8F"
GOLD = "#C9A227"
RED = "#C0392B"
ORANGE = "#D35400"
GREEN = "#1E8449"
GRAY = "#5F6F7F"
LIGHT = "#EEF3F7"


def money(n: float) -> str:
    return "$" + f"{n:,.0f}".replace(",", ".")


def millones(n: float) -> str:
    return "$" + f"{n / 1_000_000:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".") + " M"


def pct(n: float) -> str:
    return f"{n * 100:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".") + "%"


plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.edgecolor": "#D5DEE7",
    "axes.labelcolor": "#2F3B45",
    "xtick.color": "#2F3B45",
    "ytick.color": "#2F3B45",
    "axes.titlecolor": NAVY,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})


def crear_aging() -> Path:
    orden = ["Vigente", "0-30", "31-60", "61-90", ">90"]
    valores = [R["aging"][x] for x in orden]
    colores = [TEAL, GOLD, ORANGE, RED, "#7B241C"]
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    bars = ax.bar(orden, valores, color=colores, width=0.62)
    ax.set_title("Cartera por rango de vencimiento", fontsize=15, fontweight="bold", loc="left")
    ax.set_ylabel("Saldo COP")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"${x/1e6:,.0f} M"))
    ax.grid(axis="y", color="#E5E8EB", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    maxv = max(valores)
    ax.set_ylim(0, maxv * 1.22)
    for bar, v in zip(bars, valores):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + maxv * 0.03,
                millones(v), ha="center", va="bottom", fontsize=9, color=NAVY, fontweight="bold")
    fig.tight_layout()
    out = CAPTURAS / "01_aging.png"
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return out


def crear_top() -> Path:
    top = R["top_clientes"]
    nombres = [x["Nombre"] for x in top][::-1]
    valores = [x["Cartera"] for x in top][::-1]
    colores = [RED if x["Semaforo"] == "Rojo" else TEAL for x in top][::-1]
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    bars = ax.barh(nombres, valores, color=colores, height=0.55)
    ax.set_title("Top 5 clientes por saldo", fontsize=15, fontweight="bold", loc="left")
    ax.set_xlabel("Saldo COP")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"${x/1e6:,.0f} M"))
    ax.grid(axis="x", color="#E5E8EB", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    maxv = max(valores)
    ax.set_xlim(0, maxv * 1.25)
    for bar, v in zip(bars, valores):
        ax.text(bar.get_width() + maxv * 0.02, bar.get_y() + bar.get_height() / 2,
                millones(v), va="center", fontsize=9, color=NAVY, fontweight="bold")
    fig.tight_layout()
    out = CAPTURAS / "02_top_clientes.png"
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return out


def crear_conciliacion() -> Path:
    pagos = R["recaudo"]
    deposito = R["conciliacion"]["detalle_banco_sin_pago"][0]["Valor"]
    pago_sin_banco = R["conciliacion"]["detalle_pagos_sin_banco"][0]["ValorRecibido"]
    comision = abs(R["conciliacion"]["detalle_diferencias"][0]["DiferenciaBanco"])
    banco = R["conciliacion"]["total_banco"]

    labels = ["Pagos\nregistrados", "Depósito no\nidentificado", "Pago sin\nbanco", "Comisión\nbancaria", "Extracto\nbancario"]
    values = [pagos, deposito, -pago_sin_banco, -comision, banco]
    colors = [NAVY, GREEN, RED, RED, NAVY]

    bottoms = []
    running = 0.0
    for i, v in enumerate(values):
        if i == 0 or i == len(values) - 1:
            bottoms.append(0)
            running = v
        else:
            if v >= 0:
                bottoms.append(running)
                running += v
            else:
                running += v
                bottoms.append(running)
    heights = [abs(v) for v in values]

    fig, ax = plt.subplots(figsize=(8.8, 4.6))
    bars = ax.bar(labels, heights, bottom=bottoms, color=colors, width=0.58)
    ax.set_title("Puente de conciliación: pagos vs. extracto bancario", fontsize=15, fontweight="bold", loc="left")
    ax.set_ylabel("COP")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"${x/1e6:,.0f} M"))
    ax.grid(axis="y", color="#E5E8EB", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_ylim(0, max(pagos, banco) * 1.14)
    for bar, v, bottom in zip(bars, values, bottoms):
        y = bottom + abs(v) + max(pagos, banco) * 0.015
        signo = "+" if v > 0 else ("-" if v < 0 else "")
        if v in (pagos, banco):
            texto = millones(v)
        elif abs(v) < 1_000_000:
            texto = signo + money(abs(v))
        else:
            texto = signo + millones(abs(v))
        ax.text(bar.get_x() + bar.get_width() / 2, y, texto, ha="center", va="bottom", fontsize=8.5, color=NAVY, fontweight="bold")
    fig.tight_layout()
    out = CAPTURAS / "03_conciliacion.png"
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return out


def tabla_aging() -> str:
    filas = []
    total = R["cartera_total"]
    for k in ["Vigente", "0-30", "31-60", "61-90", ">90"]:
        v = R["aging"][k]
        filas.append(f"<tr><td>{k}</td><td class='num'>{money(v)}</td><td class='num'>{pct(v/total)}</td></tr>")
    filas.append(f"<tr class='total'><td>Total</td><td class='num'>{money(total)}</td><td class='num'>100,0%</td></tr>")
    return "".join(filas)


def tabla_top() -> str:
    filas = []
    for x in R["top_clientes"]:
        filas.append(
            f"<tr><td>{x['Nombre']}</td><td class='num'>{money(x['Cartera'])}</td>"
            f"<td class='num'>{pct(x['UsoCupo'])}</td><td>{x['Semaforo']}</td></tr>"
        )
    return "".join(filas)


def tabla_conciliacion() -> str:
    filas = [
        ("Depósito no identificado", "DEP-2026-999", money(R["conciliacion"]["detalle_banco_sin_pago"][0]["Valor"]), "Banco sin pago"),
        ("Pago registrado sin banco", "PAGO-0035", money(R["conciliacion"]["detalle_pagos_sin_banco"][0]["ValorRecibido"]), "Pago sin banco"),
        ("Comisión bancaria", "PAGO-0018", money(abs(R["conciliacion"]["detalle_diferencias"][0]["DiferenciaBanco"])), "Diferencia de valor"),
    ]
    return "".join(f"<tr><td>{a}</td><td>{b}</td><td class='num'>{c}</td><td>{d}</td></tr>" for a, b, c, d in filas)


def main() -> None:
    img_aging = crear_aging()
    img_top = crear_top()
    img_conc = crear_conciliacion()

    top5_concentracion = sum(x["Cartera"] for x in R["top_clientes"]) / R["cartera_total"]
    sobre_cupo = R["clientes_sobre_cupo_detalle"]

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Caso de cartera — 20 clientes</title>
<style>
@page {{
  size: Letter;
  margin: 15mm 16mm 15mm 16mm;
  @bottom-center {{
    content: "Caso de cartera · Kelvis Samir Copete Córdoba · " counter(page) " / " counter(pages);
    font-family: 'DejaVu Sans', Arial, sans-serif;
    font-size: 7.5pt;
    color: #7A828A;
  }}
}}
* {{ box-sizing: border-box; }}
body {{
  font-family: 'DejaVu Sans', Arial, sans-serif;
  color: #2F3B45;
  font-size: 9.4pt;
  line-height: 1.45;
  margin: 0;
}}
h1, h2, h3 {{ color: {NAVY}; margin: 0; }}
h1 {{ font-size: 26pt; line-height: 1.02; letter-spacing: .2px; }}
h2 {{ font-size: 15pt; margin-top: 14pt; margin-bottom: 6pt; border-bottom: 2px solid {GOLD}; padding-bottom: 3px; }}
h3 {{ font-size: 11pt; margin-top: 10pt; margin-bottom: 4pt; color: {TEAL}; }}
p {{ margin: 0 0 6pt; }}
.cover {{ min-height: 245mm; display: flex; flex-direction: column; justify-content: space-between; page-break-after: always; }}
.cover-top {{ border-top: 10px solid {NAVY}; padding-top: 20pt; }}
.kicker {{ color: {TEAL}; font-size: 10pt; font-weight: bold; letter-spacing: 1.8px; text-transform: uppercase; }}
.cover-sub {{ font-size: 12.5pt; color: {GRAY}; margin-top: 8pt; max-width: 165mm; }}
.author {{ margin-top: 20pt; font-size: 10pt; color: {GRAY}; }}
.cover-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8pt; margin-top: 20pt; }}
.toc {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 6pt; margin-top: 28pt; border-top: 1px solid #D5DEE7; border-bottom: 1px solid #D5DEE7; padding: 8pt 0; }}
.toc div {{ font-size: 7.8pt; color: {GRAY}; line-height: 1.3; }}
.toc strong {{ display: block; color: {TEAL}; font-size: 9pt; margin-bottom: 2pt; }}
.kpi {{ background: {LIGHT}; border-left: 4px solid {TEAL}; padding: 9pt 10pt; min-height: 22mm; }}
.kpi .label {{ font-size: 7.8pt; color: {GRAY}; text-transform: uppercase; letter-spacing: .5px; }}
.kpi .value {{ font-size: 16pt; font-weight: bold; color: {NAVY}; margin-top: 3pt; }}
.kpi .note {{ font-size: 7.8pt; color: {GRAY}; margin-top: 2pt; }}
.cover-bottom {{ border-top: 1px solid #D5DEE7; padding-top: 8pt; font-size: 8pt; color: {GRAY}; }}
.page-break {{ page-break-before: always; }}
table {{ width: 100%; border-collapse: collapse; margin: 6pt 0 8pt; font-size: 8.8pt; }}
th {{ background: {NAVY}; color: white; text-align: left; padding: 5pt 6pt; font-size: 8pt; }}
td {{ border-bottom: 1px solid #E1E7ED; padding: 4.5pt 6pt; vertical-align: top; }}
td.num {{ text-align: right; white-space: nowrap; }}
tr.total td {{ background: {LIGHT}; font-weight: bold; color: {NAVY}; }}
.callout {{ background: #F7F9FB; border-left: 4px solid {GOLD}; padding: 8pt 10pt; margin: 8pt 0; }}
.callout strong {{ color: {NAVY}; }}
.warn {{ border-left-color: {RED}; background: #FDF2F0; }}
.ok {{ border-left-color: {GREEN}; background: #F0FAF3; }}
.two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14pt; }}
.chart {{ display: block; width: 88%; margin: 6pt auto 8pt; }}
.small {{ font-size: 8.2pt; color: {GRAY}; }}
ul {{ margin: 4pt 0 8pt 14pt; padding: 0; }}
li {{ margin-bottom: 3pt; }}
.tag {{ display: inline-block; background: {LIGHT}; color: {NAVY}; font-size: 8pt; font-weight: bold; padding: 2pt 6pt; border-radius: 8pt; margin-right: 4pt; }}
.q {{ font-weight: bold; color: {NAVY}; margin-top: 7pt; }}
.a {{ margin: 2pt 0 7pt 0; }}
.quote {{ background: {NAVY}; color: white; padding: 12pt 14pt; margin: 10pt 0; }}
.quote p {{ color: white; margin: 0; }}
.quote .small {{ color: #CFE0EC; }}
.footer-note {{ margin-top: 12pt; padding-top: 6pt; border-top: 1px solid #D5DEE7; font-size: 7.8pt; color: {GRAY}; }}
</style>
</head>
<body>

<div class="cover">
  <div class="cover-top">
    <div class="kicker">Portafolio · Cartera y cuentas por cobrar</div>
    <h1>Caso de cartera<br>20 clientes</h1>
    <div class="cover-sub">Notas crédito y débito · aplicación de pagos · aging · conciliación bancaria · dashboard en Excel</div>
    <div class="author"><strong>Kelvis Samir Copete Córdoba</strong> · Medellín, Colombia · Corte: 30/09/2026</div>
    <div class="toc">
      <div><strong>01</strong>Contexto y alcance</div>
      <div><strong>02</strong>Cifras clave</div>
      <div><strong>03</strong>Aging y hallazgos</div>
      <div><strong>04</strong>Conciliación</div>
      <div><strong>05</strong>Entrevista</div>
    </div>
  </div>
  <div>
    <div class="cover-grid">
      <div class="kpi"><div class="label">Cartera total</div><div class="value">{millones(R['cartera_total'])}</div><div class="note">{money(R['cartera_total'])}</div></div>
      <div class="kpi"><div class="label">% vencida</div><div class="value">{pct(R['pct_vencida'])}</div><div class="note">{millones(R['cartera_vencida'])} vencidos</div></div>
      <div class="kpi"><div class="label">Recaudo</div><div class="value">{millones(R['recaudo'])}</div><div class="note">{money(R['recaudo'])}</div></div>
      <div class="kpi"><div class="label">Pagos no aplicados</div><div class="value">{millones(R['no_aplicado'])}</div><div class="note">{money(R['no_aplicado'])}</div></div>
      <div class="kpi"><div class="label">Clientes</div><div class="value">{R['clientes']}</div><div class="note">{R['facturas']} facturas · {R['pagos']} pagos</div></div>
      <div class="kpi"><div class="label">Conciliación</div><div class="value">{R['conciliacion']['conciliados']}/{R['pagos']}</div><div class="note">pagos conciliados</div></div>
    </div>
    <div class="callout"><strong>Qué demuestra:</strong> capacidad para reconstruir saldos, aplicar pagos, clasificar cartera por vencimiento, detectar clientes sobre cupo y explicar diferencias bancarias con evidencia.</div>
  </div>
  <div class="cover-bottom">Datos 100% ficticios · Distribuciones Andinas S.A.S. · Workbook: Cartera_20_Clientes.xlsx · Guía: Guia_Caso_Cartera.pdf · github.com/Samircopete12/cartera-clientes</div>
</div>

<h2>1. Contexto y objetivo</h2>
<p><strong>Distribuciones Andinas S.A.S.</strong> es una empresa ficticia de suministros corporativos. La cartera está dispersa en 20 clientes, con facturas a 15, 30, 45 y 60 días, notas crédito y débito, pagos parciales y movimientos bancarios que no siempre coinciden con los recaudos registrados.</p>
<p><strong>Objetivo:</strong> ordenar la cartera al corte del 30/09/2026, reconstruir el saldo por factura, aplicar pagos, clasificar el aging, identificar clientes sobre cupo y conciliar el extracto bancario contra los pagos registrados.</p>
<div class="callout"><strong>Regla base:</strong> Saldo de factura = valor factura − notas crédito + notas débito − pagos aplicados. Un pago no aplicado no reduce la cartera; queda como partida pendiente de identificar.</div>

<h2>2. Alcance del caso</h2>
<div class="two-col">
  <table>
    <tr><th>Dato</th><th>Cantidad</th></tr>
    <tr><td>Clientes</td><td class="num">{R['clientes']}</td></tr>
    <tr><td>Facturas</td><td class="num">{R['facturas']}</td></tr>
    <tr><td>Notas crédito</td><td class="num">{R['notas_credito']}</td></tr>
    <tr><td>Notas débito</td><td class="num">{R['notas_debito']}</td></tr>
    <tr><td>Pagos</td><td class="num">{R['pagos']}</td></tr>
    <tr><td>Aplicaciones de pago</td><td class="num">{R['aplicaciones']}</td></tr>
    <tr><td>Movimientos bancarios</td><td class="num">{R['movimientos_banco']}</td></tr>
  </table>
  <div>
    <p><span class="tag">Excel</span><span class="tag">Python/pandas</span><span class="tag">Validación</span></p>
    <p>El workbook tiene 12 hojas: Inicio, Dashboard, Cartera, Aging, Conciliación, Pagos, Notas, Facturas, Clientes, Aplicación, Extracto y Validación.</p>
    <p>Las cifras se calculan con fórmulas, no con valores escritos a mano. La hoja <strong>Validación</strong> comprueba los cuadres principales.</p>
  </div>
</div>

<h2>3. Cifras clave</h2>
<table>
  <tr><th>Rango</th><th>Saldo</th><th>% cartera</th></tr>
  {tabla_aging()}
</table>
<p class="small">La cartera vencida asciende a {money(R['cartera_vencida'])} ({pct(R['pct_vencida'])} del total). El rango <strong>&gt;90 días</strong> concentra {money(R['aging']['>90'])} ({pct(R['aging']['>90']/R['cartera_total'])}).</p>

<h2>4. Hallazgos principales</h2>
<ul>
  <li><strong>85,5% de la cartera está vencida.</strong> No es solo un problema de cobro: hay facturas de abril y mayo que siguen abiertas.</li>
  <li><strong>{R['clientes_sobre_cupo']} clientes superan su cupo:</strong> {sobre_cupo[0]['Nombre']} ({pct(sobre_cupo[0]['UsoCupo'])}), {sobre_cupo[1]['Nombre']} ({pct(sobre_cupo[1]['UsoCupo'])}) y {sobre_cupo[2]['Nombre']} ({pct(sobre_cupo[2]['UsoCupo'])}).</li>
  <li><strong>Top 5 concentra {pct(top5_concentracion)} de la cartera.</strong> La prioridad de cobro no puede ser solo por saldo: hay que cruzar cupo, días vencidos y comportamiento de pago.</li>
  <li><strong>{len(R['pagos_no_aplicados'])} pagos tienen saldo sin aplicar por {money(R['no_aplicado'])}.</strong> Ese dinero ya entró, pero no está reduciendo la factura correcta.</li>
  <li><strong>33 de 35 pagos están conciliados.</strong> Quedan 3 partidas: un depósito no identificado, un pago sin registro bancario y una comisión bancaria.</li>
</ul>

<h2>5. Aging y concentración</h2>
<img class="chart" src="{img_aging}">
<img class="chart" src="{img_top}">
<p class="small">Los clientes en rojo superan el cupo asignado. El top 5 se calcula por saldo total, no por saldo vencido.</p>

<h2>6. Conciliación bancaria</h2>
<p>El extracto bancario totaliza {money(R['conciliacion']['total_banco'])}, mientras que los pagos registrados suman {money(R['recaudo'])}. La diferencia neta es <strong>{money(R['conciliacion']['diferencia'])}</strong> y se explica por tres partidas:</p>
<table>
  <tr><th>Partida</th><th>Referencia</th><th>Valor</th><th>Estado</th></tr>
  {tabla_conciliacion()}
</table>
<img class="chart" src="{img_conc}">
<div class="callout warn"><strong>Hallazgo de control:</strong> el depósito de {money(R['conciliacion']['detalle_banco_sin_pago'][0]['Valor'])} no tiene pago asociado. Antes de aplicarlo a cartera hay que identificar al cliente y la factura; no se debe abonar a ciegas.</div>

<h2>7. Preguntas de entrevista y respuestas guía</h2>
<div class="q">1. ¿Qué es un pago no aplicado?</div>
<div class="a">Es un recaudo que ya entró al banco pero todavía no se cruzó contra una factura. En el caso hay {money(R['no_aplicado'])} en esa situación. Se investiga, se identifica el cliente y se aplica; mientras tanto no reduce la cartera.</div>
<div class="q">2. ¿Cómo calculás el saldo de una factura?</div>
<div class="a">Valor factura − notas crédito + notas débito − pagos aplicados. Las notas crédito disminuyen el saldo; las notas débito lo aumentan. Los pagos no aplicados no se restan.</div>
<div class="q">3. ¿Qué es el aging y para qué sirve?</div>
<div class="a">Es la clasificación de la cartera por días vencidos: vigente, 0-30, 31-60, 61-90 y más de 90. Sirve para priorizar cobro, estimar riesgo y detectar clientes que se están financiando con la empresa.</div>
<div class="q">4. ¿Qué cliente priorizarías?</div>
<div class="a">Empezaría por {sobre_cupo[0]['Nombre']}: tiene {money(sobre_cupo[0]['Cartera'])}, usa {pct(sobre_cupo[0]['UsoCupo'])} de su cupo y combina saldo alto con exceso de cupo. Luego revisaría {sobre_cupo[1]['Nombre']} y {sobre_cupo[2]['Nombre']}.</div>
<div class="q">5. ¿Cómo conciliás el banco contra cartera?</div>
<div class="a">Cruzo referencia, fecha y valor; separo pagos conciliados, pagos sin registro bancario, depósitos no identificados y diferencias de valor. Cada diferencia debe tener una explicación y un responsable.</div>
<div class="q">6. ¿Qué diferencia hay entre nota crédito y nota débito?</div>
<div class="a">La nota crédito reduce el saldo del cliente (devolución, descuento o error). La nota débito lo aumenta (flete, interés o ajuste). Ambas deben quedar asociadas a una factura y a un motivo.</div>
<div class="q">7. ¿Qué mejorarías del proceso?</div>
<div class="a">Aplicaría pagos el mismo día, establecería un control semanal de pagos no aplicados, revisaría cupos antes de facturar y haría conciliación bancaria diaria o semanal, no al cierre.</div>

<h2>8. Cómo explicarlo en 3 minutos</h2>
<div class="quote">
<p><strong>“Armé un caso de cartera con 20 clientes y 50 facturas para practicar el ciclo completo: notas crédito y débito, aplicación de pagos, aging y conciliación bancaria.”</strong></p>
<p class="small">“El caso tiene {money(R['cartera_total'])} de cartera, de los cuales {pct(R['pct_vencida'])} está vencida. Detecté {R['clientes_sobre_cupo']} clientes sobre cupo, {money(R['no_aplicado'])} en pagos no aplicados y 3 partidas de conciliación. El dashboard prioriza cobro por saldo, vencimiento y uso de cupo. Lo construí en Excel con fórmulas y lo validé con Python; la hoja de validación cierra los cuadres.”</p>
</div>
<p><strong>Énfasis para la entrevista:</strong> no digas “hice un Excel”. Decí “reconstruí la cartera, expliqué las diferencias y propuse acciones de cobro”.</p>

<h2>9. Límites y notas de honestidad</h2>
<ul>
  <li>Todos los datos son ficticios; no se usó información real de empresas.</li>
  <li>El caso es un ejercicio de cartera en Excel, no una implementación en SAP. No se reclama experiencia en SAP.</li>
  <li>La conciliación es un caso didáctico: en producción se debe validar contra el ERP, el banco y los soportes.</li>
  <li>Las decisiones de cobro requieren validación humana y revisión comercial.</li>
</ul>

<h2>10. Archivos del caso</h2>
<table>
  <tr><th>Archivo</th><th>Uso</th></tr>
  <tr><td>Cartera_20_Clientes.xlsx</td><td>Workbook con dashboard, cartera, aging, conciliación y validación.</td></tr>
  <tr><td>Guia_Caso_Cartera.pdf</td><td>Esta guía: contexto, cifras, hallazgos y respuestas de entrevista.</td></tr>
  <tr><td>datos/*.csv</td><td>Datos fuente sintéticos y reproducibles.</td></tr>
  <tr><td>scripts/*.py</td><td>Generación de datos, cálculo, workbook y guía.</td></tr>
  <tr><td>capturas/*.png</td><td>Gráficas para portafolio y README.</td></tr>
</table>
<div class="footer-note">Caso preparado para el portafolio de Kelvis Samir Copete Córdoba · Medellín, 2026 · Datos ficticios.</div>

</body>
</html>"""

    html_path = BASE / "Guia_Caso_Cartera.html"
    pdf_path = BASE / "Guia_Caso_Cartera.pdf"
    html_path.write_text(html, encoding="utf-8")
    HTML(string=html, base_url=str(BASE)).write_pdf(str(pdf_path))
    print(f"OK: {pdf_path}")
    print(f"OK: {html_path}")


if __name__ == "__main__":
    main()
