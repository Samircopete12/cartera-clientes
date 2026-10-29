#!/usr/bin/env python3
"""Genera el caso sintético de cartera de 20 clientes.

Todos los datos son ficticios. El corte contable es el 30/09/2026.
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

BASE = Path("/home/rimas/cartera-clientes")
DATOS = BASE / "datos"
DATOS.mkdir(parents=True, exist_ok=True)

CORTE = date(2026, 9, 30)
random.seed(20260930)

CLIENTES = [
    ("C001", "Almacén Central S.A.S.", "900.123.456-1", "Medellín", 25_000_000, 30),
    ("C002", "Distribuidora El Poblado", "901.234.567-2", "Medellín", 18_000_000, 30),
    ("C003", "Ferretería La 80", "890.345.678-3", "Medellín", 12_000_000, 45),
    ("C004", "Suministros Antioquia", "900.456.789-4", "Itagüí", 20_000_000, 30),
    ("C005", "Papelería Modelo", "901.567.890-5", "Bello", 8_000_000, 30),
    ("C006", "Constructora Andina", "890.678.901-6", "Medellín", 35_000_000, 60),
    ("C007", "Hotel Mirador", "900.789.012-7", "Medellín", 15_000_000, 45),
    ("C008", "Clínica San Lucas", "901.890.123-8", "Envigado", 22_000_000, 30),
    ("C009", "Colegio Nuevo Horizonte", "890.901.234-9", "Sabaneta", 10_000_000, 45),
    ("C010", "Supermercado La Estrella", "900.012.345-0", "La Estrella", 14_000_000, 30),
    ("C011", "Talleres Jaramillo", "901.123.456-1", "Medellín", 9_000_000, 30),
    ("C012", "Restaurante El Trapiche", "890.234.567-2", "Medellín", 7_000_000, 15),
    ("C013", "Textiles Rionegro", "900.345.678-3", "Rionegro", 28_000_000, 60),
    ("C014", "Laboratorio Vital", "901.456.789-4", "Medellín", 16_000_000, 45),
    ("C015", "Centro Médico del Sur", "890.567.890-5", "Envigado", 13_000_000, 30),
    ("C016", "Oficinas Premium", "900.678.901-6", "Medellín", 11_000_000, 30),
    ("C017", "Transportes Cargo Sur", "901.789.012-7", "Caldas", 19_000_000, 45),
    ("C018", "Panadería La Espiga", "890.890.123-8", "Bello", 5_000_000, 15),
    ("C019", "Farmacia Central", "900.901.234-9", "Medellín", 12_000_000, 30),
    ("C020", "Imprenta Aurora", "901.012.345-0", "Medellín", 8_000_000, 30),
]

MOTIVOS_NC = [
    "Devolución de mercancía",
    "Descuento comercial",
    "Error de facturación",
    "Ajuste por producto defectuoso",
]
MOTIVOS_ND = [
    "Flete adicional",
    "Intereses de mora",
    "Ajuste de precio",
    "Cargo por embalaje",
]
MEDIOS = ["Transferencia", "PSE", "Cheque", "Efectivo"]
BANCOS = ["Bancolombia", "Davivienda", "BBVA", "Banco de Bogotá"]


def fecha_aleatoria(inicio: date, fin: date) -> date:
    return inicio + timedelta(days=random.randint(0, (fin - inicio).days))


def redondear_miles(valor: float) -> int:
    return max(1000, int(round(valor / 1000.0) * 1000))


def main() -> None:
    # 1. Clientes
    clientes = [
        {
            "ClienteID": cid,
            "Nombre": nombre,
            "NIT": nit,
            "Ciudad": ciudad,
            "CupoCredito": cupo,
            "PlazoDias": plazo,
        }
        for cid, nombre, nit, ciudad, cupo, plazo in CLIENTES
    ]

    # 2. Facturas: 50, todas las 20 empresas tienen al menos una.
    facturas = []
    for i in range(50):
        if i < 20:
            cliente = clientes[i]
        else:
            cliente = random.choice(clientes)
        fecha_factura = fecha_aleatoria(date(2026, 4, 1), date(2026, 9, 20))
        vencimiento = fecha_factura + timedelta(days=cliente["PlazoDias"])
        valor = redondear_miles(random.uniform(800_000, 7_800_000))
        facturas.append(
            {
                "FacturaID": f"FV-2026-{i + 1:03d}",
                "ClienteID": cliente["ClienteID"],
                "FechaFactura": fecha_factura.isoformat(),
                "FechaVencimiento": vencimiento.isoformat(),
                "ValorFactura": valor,
                "Concepto": random.choice(
                    ["Venta de mercancía", "Servicio de suministro", "Pedido corporativo"]
                ),
            }
        )

    # 3. Notas crédito: 8, sobre facturas distintas.
    facturas_nc = random.sample(facturas, 8)
    notas_credito = []
    for i, f in enumerate(facturas_nc, start=1):
        valor = redondear_miles(f["ValorFactura"] * random.uniform(0.05, 0.18))
        fecha = date.fromisoformat(f["FechaFactura"]) + timedelta(days=random.randint(5, 20))
        notas_credito.append(
            {
                "NotaCreditoID": f"NC-2026-{i:03d}",
                "FacturaID": f["FacturaID"],
                "ClienteID": f["ClienteID"],
                "Fecha": fecha.isoformat(),
                "Valor": valor,
                "Motivo": random.choice(MOTIVOS_NC),
            }
        )

    # 4. Notas débito: 6, sobre facturas distintas de las anteriores.
    facturas_nd = random.sample([f for f in facturas if f not in facturas_nc], 6)
    notas_debito = []
    for i, f in enumerate(facturas_nd, start=1):
        valor = redondear_miles(f["ValorFactura"] * random.uniform(0.02, 0.08))
        fecha = date.fromisoformat(f["FechaFactura"]) + timedelta(days=random.randint(5, 20))
        notas_debito.append(
            {
                "NotaDebitoID": f"ND-2026-{i:03d}",
                "FacturaID": f["FacturaID"],
                "ClienteID": f["ClienteID"],
                "Fecha": fecha.isoformat(),
                "Valor": valor,
                "Motivo": random.choice(MOTIVOS_ND),
            }
        )

    # 5. Pagos y aplicaciones.
    nc_por_factura = {n["FacturaID"]: n["Valor"] for n in notas_credito}
    nd_por_factura = {n["FacturaID"]: n["Valor"] for n in notas_debito}
    aplicado_por_factura = {f["FacturaID"]: 0 for f in facturas}

    def saldo_disponible(f: dict) -> int:
        return max(
            0,
            f["ValorFactura"]
            - nc_por_factura.get(f["FacturaID"], 0)
            + nd_por_factura.get(f["FacturaID"], 0)
            - aplicado_por_factura[f["FacturaID"]],
        )

    pagos = []
    aplicaciones = []
    extra_no_aplicado = {3: 180_000, 11: 320_000, 23: 150_000, 31: 420_000}

    for i in range(1, 36):
        # Buscar un cliente con facturas disponibles.
        candidatos = []
        for cliente in clientes:
            disponibles = [
                f
                for f in facturas
                if f["ClienteID"] == cliente["ClienteID"] and saldo_disponible(f) > 50_000
            ]
            if disponibles:
                candidatos.append((cliente, disponibles))
        if not candidatos:
            break
        cliente, disponibles = random.choice(candidatos)
        seleccionadas = random.sample(disponibles, k=min(len(disponibles), random.choice([1, 1, 1, 2])))

        # La fecha del pago debe ser posterior a las notas y a la factura.
        fecha_min = max(date.fromisoformat(f["FechaFactura"]) for f in seleccionadas) + timedelta(days=21)
        for f in seleccionadas:
            for n in notas_credito + notas_debito:
                if n["FacturaID"] == f["FacturaID"]:
                    fecha_min = max(fecha_min, date.fromisoformat(n["Fecha"]) + timedelta(days=1))
        if fecha_min >= CORTE:
            continue
        fecha_pago = fecha_aleatoria(fecha_min, CORTE - timedelta(days=1))

        valor_aplicado_total = 0
        for f in seleccionadas:
            disponible = saldo_disponible(f)
            if disponible <= 0:
                continue
            factor = random.choice([0.45, 0.60, 0.75, 0.90, 1.00])
            valor = redondear_miles(disponible * factor)
            valor = min(valor, disponible)
            if valor < 1000:
                continue
            aplicado_por_factura[f["FacturaID"]] += valor
            valor_aplicado_total += valor
            aplicaciones.append(
                {
                    "PagoID": f"RC-2026-{i:03d}",
                    "FacturaID": f["FacturaID"],
                    "ClienteID": f["ClienteID"],
                    "FechaAplicacion": fecha_pago.isoformat(),
                    "ValorAplicado": valor,
                }
            )

        if valor_aplicado_total == 0:
            continue

        extra = extra_no_aplicado.get(i, 0)
        valor_recibido = valor_aplicado_total + extra
        pagos.append(
            {
                "PagoID": f"RC-2026-{i:03d}",
                "ClienteID": cliente["ClienteID"],
                "Fecha": fecha_pago.isoformat(),
                "ValorRecibido": valor_recibido,
                "Medio": random.choice(MEDIOS),
                "Banco": random.choice(BANCOS),
                "Referencia": f"PAGO-{i:04d}",
                "Observacion": "Recaudo aplicado a facturas" if extra == 0 else "Incluye valor pendiente de aplicar",
            }
        )

    # 6. Extracto bancario.
    extracto = []
    for p in pagos:
        if p["PagoID"] == "RC-2026-035":
            continue  # Pago registrado en cartera pero no aparece en banco.
        fecha_banco = date.fromisoformat(p["Fecha"]) + timedelta(days=random.choice([0, 0, 1]))
        valor_banco = p["ValorRecibido"]
        descripcion = "Recaudo transferencia"
        if p["PagoID"] == "RC-2026-018":
            valor_banco -= 25_000
            descripcion = "Recaudo neto - comisión bancaria"
        extracto.append(
            {
                "Fecha": fecha_banco.isoformat(),
                "Referencia": p["Referencia"],
                "Descripcion": descripcion,
                "Valor": valor_banco,
                "Tipo": "Depósito",
            }
        )

    extracto.append(
        {
            "Fecha": "2026-09-28",
            "Referencia": "DEP-2026-999",
            "Descripcion": "Transferencia no identificada",
            "Valor": 1_250_000,
            "Tipo": "Depósito",
        }
    )
    extracto.sort(key=lambda x: (x["Fecha"], x["Referencia"]))

    # 7. Escribir CSV.
    def escribir(nombre: str, filas: list[dict]) -> None:
        with (DATOS / nombre).open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
            writer.writeheader()
            writer.writerows(filas)

    escribir("clientes.csv", clientes)
    escribir("facturas.csv", facturas)
    escribir("notas_credito.csv", notas_credito)
    escribir("notas_debito.csv", notas_debito)
    escribir("pagos.csv", pagos)
    escribir("aplicacion_pagos.csv", aplicaciones)
    escribir("extracto_bancario.csv", extracto)

    # 8. Resumen de control.
    total_facturado = sum(f["ValorFactura"] for f in facturas)
    total_nc = sum(n["Valor"] for n in notas_credito)
    total_nd = sum(n["Valor"] for n in notas_debito)
    total_recaudo = sum(p["ValorRecibido"] for p in pagos)
    total_aplicado = sum(a["ValorAplicado"] for a in aplicaciones)
    cartera = total_facturado - total_nc + total_nd - total_aplicado
    total_banco = sum(e["Valor"] for e in extracto)
    print(f"Clientes: {len(clientes)}")
    print(f"Facturas: {len(facturas)} | Facturado: {total_facturado:,.0f}")
    print(f"Notas crédito: {len(notas_credito)} | {total_nc:,.0f}")
    print(f"Notas débito: {len(notas_debito)} | {total_nd:,.0f}")
    print(f"Pagos: {len(pagos)} | Recaudo: {total_recaudo:,.0f} | Aplicado: {total_aplicado:,.0f}")
    print(f"Pagos no aplicados: {total_recaudo - total_aplicado:,.0f}")
    print(f"Cartera: {cartera:,.0f}")
    print(f"Extracto: {len(extracto)} | Banco: {total_banco:,.0f}")
    print(f"Diferencia banco - pagos: {total_banco - total_recaudo:,.0f}")


if __name__ == "__main__":
    main()
