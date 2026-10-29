#!/usr/bin/env python3
"""Calcula las cifras del caso y guarda datos/resumen.json."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

BASE = Path("/home/rimas/cartera-clientes")
DATOS = BASE / "datos"
CORTE = pd.Timestamp("2026-09-30")


def main() -> None:
    clientes = pd.read_csv(DATOS / "clientes.csv")
    facturas = pd.read_csv(DATOS / "facturas.csv")
    nc = pd.read_csv(DATOS / "notas_credito.csv")
    nd = pd.read_csv(DATOS / "notas_debito.csv")
    pagos = pd.read_csv(DATOS / "pagos.csv")
    aplicacion = pd.read_csv(DATOS / "aplicacion_pagos.csv")
    extracto = pd.read_csv(DATOS / "extracto_bancario.csv")

    nc_sum = nc.groupby("FacturaID")["Valor"].sum()
    nd_sum = nd.groupby("FacturaID")["Valor"].sum()
    ap_sum = aplicacion.groupby("FacturaID")["ValorAplicado"].sum()

    facturas["NotasCredito"] = facturas["FacturaID"].map(nc_sum).fillna(0)
    facturas["NotasDebito"] = facturas["FacturaID"].map(nd_sum).fillna(0)
    facturas["PagosAplicados"] = facturas["FacturaID"].map(ap_sum).fillna(0)
    facturas["Saldo"] = (
        facturas["ValorFactura"]
        - facturas["NotasCredito"]
        + facturas["NotasDebito"]
        - facturas["PagosAplicados"]
    )
    facturas["FechaVencimiento"] = pd.to_datetime(facturas["FechaVencimiento"])
    facturas["DiasVencidos"] = (CORTE - facturas["FechaVencimiento"]).dt.days.clip(lower=0)
    facturas["Estado"] = facturas.apply(
        lambda r: "Pagada" if r["Saldo"] <= 0 else ("Vigente" if r["DiasVencidos"] == 0 else "Vencida"),
        axis=1,
    )

    def rango(row: pd.Series) -> str:
        if row["Saldo"] <= 0:
            return "Pagada"
        if row["DiasVencidos"] == 0:
            return "Vigente"
        if row["DiasVencidos"] <= 30:
            return "0-30"
        if row["DiasVencidos"] <= 60:
            return "31-60"
        if row["DiasVencidos"] <= 90:
            return "61-90"
        return ">90"

    facturas["Rango"] = facturas.apply(rango, axis=1)

    cartera_total = float(facturas["Saldo"].sum())
    vencida = float(facturas.loc[facturas["Estado"] == "Vencida", "Saldo"].sum())
    vigente = cartera_total - vencida
    total_facturado = float(facturas["ValorFactura"].sum())
    total_nc = float(nc["Valor"].sum())
    total_nd = float(nd["Valor"].sum())
    total_recaudo = float(pagos["ValorRecibido"].sum())
    total_aplicado = float(aplicacion["ValorAplicado"].sum())
    no_aplicado = total_recaudo - total_aplicado
    cupo_total = float(clientes["CupoCredito"].sum())

    aging = {
        "Vigente": float(facturas.loc[facturas["Rango"] == "Vigente", "Saldo"].sum()),
        "0-30": float(facturas.loc[facturas["Rango"] == "0-30", "Saldo"].sum()),
        "31-60": float(facturas.loc[facturas["Rango"] == "31-60", "Saldo"].sum()),
        "61-90": float(facturas.loc[facturas["Rango"] == "61-90", "Saldo"].sum()),
        ">90": float(facturas.loc[facturas["Rango"] == ">90", "Saldo"].sum()),
    }

    por_cliente = facturas.groupby("ClienteID")["Saldo"].sum().reset_index(name="Cartera")
    vencida_cliente = facturas.loc[facturas["Estado"] == "Vencida"].groupby("ClienteID")["Saldo"].sum()
    por_cliente["Vencida"] = por_cliente["ClienteID"].map(vencida_cliente).fillna(0)
    por_cliente = por_cliente.merge(clientes[["ClienteID", "Nombre", "CupoCredito"]], on="ClienteID", how="left")
    por_cliente["Cartera"] = por_cliente["Cartera"].astype(float)
    por_cliente["Vencida"] = por_cliente["Vencida"].astype(float)
    por_cliente["CupoCredito"] = por_cliente["CupoCredito"].astype(float)
    por_cliente["UsoCupo"] = por_cliente["Cartera"] / por_cliente["CupoCredito"]
    por_cliente["Semaforo"] = por_cliente["UsoCupo"].apply(lambda x: "Rojo" if x > 1 else ("Amarillo" if x >= 0.8 else "Verde"))
    por_cliente = por_cliente.sort_values("Cartera", ascending=False)

    pagos["Aplicado"] = pagos["PagoID"].map(aplicacion.groupby("PagoID")["ValorAplicado"].sum()).fillna(0)
    pagos["NoAplicado"] = pagos["ValorRecibido"] - pagos["Aplicado"]
    pagos["ValorBanco"] = pagos["Referencia"].map(extracto.groupby("Referencia")["Valor"].sum()).fillna(0)
    pagos["DiferenciaBanco"] = pagos["ValorBanco"] - pagos["ValorRecibido"]
    pagos["EstadoConciliacion"] = pagos.apply(
        lambda r: "Pago sin banco" if r["ValorBanco"] == 0 else ("Conciliado" if abs(r["DiferenciaBanco"]) < 1 else "Diferencia de valor"),
        axis=1,
    )
    pagos_con_no_aplicado = pagos.loc[pagos["NoAplicado"] > 0, ["PagoID", "ClienteID", "Fecha", "ValorRecibido", "Aplicado", "NoAplicado"]]
    pagos_sin_banco = pagos.loc[pagos["EstadoConciliacion"] == "Pago sin banco"]
    diferencias_valor = pagos.loc[pagos["EstadoConciliacion"] == "Diferencia de valor"]
    banco_sin_pago = extracto.loc[~extracto["Referencia"].isin(pagos["Referencia"])]

    resumen = {
        "corte": "2026-09-30",
        "clientes": int(len(clientes)),
        "facturas": int(len(facturas)),
        "notas_credito": int(len(nc)),
        "notas_debito": int(len(nd)),
        "pagos": int(len(pagos)),
        "aplicaciones": int(len(aplicacion)),
        "movimientos_banco": int(len(extracto)),
        "facturado": total_facturado,
        "notas_credito_valor": total_nc,
        "notas_debito_valor": total_nd,
        "recaudo": total_recaudo,
        "aplicado": total_aplicado,
        "no_aplicado": no_aplicado,
        "cartera_total": cartera_total,
        "cartera_vencida": vencida,
        "cartera_vigente": vigente,
        "pct_vencida": vencida / cartera_total if cartera_total else 0,
        "cupo_total": cupo_total,
        "pct_cupo_usado": cartera_total / cupo_total if cupo_total else 0,
        "clientes_con_saldo": int((por_cliente["Cartera"] > 0).sum()),
        "clientes_sobre_cupo": int((por_cliente["Semaforo"] == "Rojo").sum()),
        "facturas_con_saldo": int((facturas["Saldo"] > 0).sum()),
        "aging": aging,
        "top_clientes": por_cliente.head(5)[["ClienteID", "Nombre", "Cartera", "UsoCupo", "Semaforo"]].to_dict(orient="records"),
        "clientes_sobre_cupo_detalle": por_cliente.loc[por_cliente["Semaforo"] == "Rojo", ["ClienteID", "Nombre", "Cartera", "CupoCredito", "UsoCupo"]].to_dict(orient="records"),
        "pagos_no_aplicados": pagos_con_no_aplicado.to_dict(orient="records"),
        "conciliacion": {
            "total_banco": float(extracto["Valor"].sum()),
            "diferencia": float(extracto["Valor"].sum() - total_recaudo),
            "conciliados": int((pagos["EstadoConciliacion"] == "Conciliado").sum()),
            "pagos_sin_banco": int(len(pagos_sin_banco)),
            "diferencias_valor": int(len(diferencias_valor)),
            "banco_sin_pago": int(len(banco_sin_pago)),
            "detalle_pagos_sin_banco": pagos_sin_banco[["PagoID", "Referencia", "Fecha", "ValorRecibido"]].to_dict(orient="records"),
            "detalle_diferencias": diferencias_valor[["PagoID", "Referencia", "ValorRecibido", "ValorBanco", "DiferenciaBanco"]].to_dict(orient="records"),
            "detalle_banco_sin_pago": banco_sin_pago[["Fecha", "Referencia", "Descripcion", "Valor"]].to_dict(orient="records"),
        },
    }

    with (DATOS / "resumen.json").open("w", encoding="utf-8") as fh:
        json.dump(resumen, fh, ensure_ascii=False, indent=2)

    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
