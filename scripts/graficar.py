#!/usr/bin/env python3
"""Gráficas del benchmark: tiempo, speedup, eficiencia y escalabilidad débil.
Uso: python3 scripts/graficar.py [EQUIPO]   (L, AUX o LAB)"""
import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

equipo = sys.argv[1] if len(sys.argv) > 1 else "L"
ruta = f"docs/evidencias/resultados/benchmark_{equipo}.csv"
dir_g = "docs/evidencias/graficas"
os.makedirs(dir_g, exist_ok=True)

df = pd.read_csv(ruta)
df = df[df["hash_ok"] != "DIFIERE"]
med = df.groupby(["modo", "N", "nsims", "hilos", "procs"], as_index=False)["tiempo_s"].min()
med["p"] = med["hilos"] * med["procs"]

def base(modo, N):
    m = "mpi" if modo == "hibrido" else modo
    return med[(med["modo"] == m) & (med["N"] == N) & (med["p"] == 1)].iloc[0]["tiempo_s"]

t1v = med[med["modo"] == "vigia_seq"].iloc[0]["tiempo_s"]

filas = []
for r in med.itertuples():
    if r.modo in ("omp", "mpi", "hibrido"):
        caso, t1, orden = f"Autómata N={r.N}", base(r.modo, r.N), r.N
    elif r.modo == "vigia_fuerte":
        caso, t1, orden = f"Vigía N={r.N}, {r.nsims} sims", t1v, 10**9
    else:
        continue
    sp = t1 / r.tiempo_s
    filas.append({"equipo": equipo, "caso": caso, "orden": orden, "modo": r.modo,
                  "p": r.p, "hilos": r.hilos, "procs": r.procs,
                  "tiempo_s": r.tiempo_s, "speedup": sp, "eficiencia": sp / r.p})
fu = pd.DataFrame(filas).sort_values(["orden", "modo", "p"])
casos = list(dict.fromkeys(fu["caso"]))


def figura(col, titulo, ylabel, archivo, ideal):
    fig, axes = plt.subplots(1, len(casos), figsize=(4.2 * len(casos), 3.8), squeeze=False)
    for ax, caso in zip(axes[0], casos):
        d = fu[fu["caso"] == caso]
        for modo, g in d.groupby("modo"):
            ax.plot(g["p"], g[col], marker="o", label=modo)
        ps = sorted(d["p"].unique())
        if ideal == "lineal":
            ax.plot(ps, ps, "k--", lw=1, label="ideal")
        elif ideal == "uno":
            ax.axhline(1.0, color="k", ls="--", lw=1, label="ideal")
            ax.set_ylim(0, 1.3)
        ax.set_xticks(ps)
        ax.set_title(caso, fontsize=10)
        ax.set_xlabel("hilos x procesos (p)")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)
    axes[0][0].legend(fontsize=8)
    fig.suptitle(f"{titulo} - equipo {equipo}")
    fig.tight_layout()
    fig.savefig(f"{dir_g}/{archivo}_{equipo}.png", dpi=110)
    plt.close(fig)


figura("tiempo_s", "Tiempo de ejecución", "tiempo (s)", "tiempo", None)
figura("speedup", "Speedup Sp = T1/Tp (escalabilidad fuerte)", "Sp", "speedup", "lineal")
figura("eficiencia", "Eficiencia Ep = Sp/p", "Ep", "eficiencia", "uno")

# Escalabilidad débil (Gustafson): las simulaciones del Vigía crecen con los procesos
d = med[med["modo"] == "vigia_debil"].sort_values("procs")
if len(d):
    t1w = d.iloc[0]["tiempo_s"]
    d = d.assign(escalado=d["procs"] * t1w / d["tiempo_s"], ef_debil=t1w / d["tiempo_s"])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.8))
    a1.plot(d["procs"], d["tiempo_s"], marker="o", label="medido")
    a1.axhline(t1w, color="k", ls="--", lw=1, label="ideal (constante)")
    a1.set_ylabel("tiempo (s)")
    a2.plot(d["procs"], d["escalado"], marker="o", label="medido")
    a2.plot(d["procs"], d["procs"], "k--", lw=1, label="ideal")
    a2.set_ylabel("speedup escalado p*T(1)/T(p)")
    for ax in (a1, a2):
        ax.set_xticks(list(d["procs"]))
        ax.set_xlabel("procesos (simulaciones = base x p)")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    fig.suptitle(f"Escalabilidad débil del Vigía - equipo {equipo}")
    fig.tight_layout()
    fig.savefig(f"{dir_g}/debil_{equipo}.png", dpi=110)
    plt.close(fig)
    d.to_csv(f"docs/evidencias/resultados/metricas_debil_{equipo}.csv", index=False)

fu.drop(columns="orden").to_csv(f"docs/evidencias/resultados/metricas_{equipo}.csv", index=False)
print(fu.drop(columns=["orden", "equipo"]).round(3).to_string(index=False))
if len(d):
    print()
    print(d[["procs", "nsims", "tiempo_s", "escalado", "ef_debil"]].round(3).to_string(index=False))
print(f"\nGráficas en {dir_g}/ (tiempo, speedup, eficiencia, debil) para el equipo {equipo}")
