#!/usr/bin/env python3
"""Ajuste de la Ley de Amdahl (escalabilidad fuerte) y de Gustafson (débil).
Uso: python3 scripts/ajuste.py [EQUIPO]   (lee metricas_<EQUIPO>.csv y metricas_debil_<EQUIPO>.csv)"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

equipo = sys.argv[1] if len(sys.argv) > 1 else "L"
res = "docs/evidencias/resultados"
fu = pd.read_csv(f"{res}/metricas_{equipo}.csv")
db = pd.read_csv(f"{res}/metricas_debil_{equipo}.csv")


def amdahl(p, f):
    return 1.0 / (f + (1.0 - f) / p)


def ajustar(p, sp):
    fs = np.linspace(0.0, 1.0, 10001)
    err = [np.sum((amdahl(p, f) - sp) ** 2) for f in fs]
    i = int(np.argmin(err))
    return fs[i], float(np.sqrt(err[i] / len(p)))


filas = []
casos = list(dict.fromkeys(fu["caso"]))
fig, axes = plt.subplots(1, len(casos), figsize=(4.2 * len(casos), 3.8), squeeze=False)
for ax, caso in zip(axes[0], casos):
    d = fu[fu["caso"] == caso]
    # un solo valor por p: el mejor speedup medido (mpi/omp/hibrido comparten p)
    g = d.groupby("p", as_index=False)["speedup"].max()
    p = g["p"].to_numpy(float)
    sp = g["speedup"].to_numpy(float)
    f, rmse = ajustar(p, sp)
    filas.append({"equipo": equipo, "caso": caso, "f_amdahl": round(f, 4),
                  "sp_max_teorico": round(1.0 / f, 2) if f > 0 else float("inf"),
                  "rmse": round(rmse, 4)})
    pp = np.linspace(1, max(p), 50)
    ax.plot(p, sp, "o", label="medido")
    ax.plot(pp, amdahl(pp, f), "-", label=f"Amdahl f={f:.3f}")
    ax.plot(pp, pp, "k--", lw=1, label="ideal")
    ax.set_title(caso, fontsize=10)
    ax.set_xlabel("p")
    ax.set_ylabel("Sp")
    ax.set_xticks(sorted(set(p)))
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
fig.suptitle(f"Ajuste de la Ley de Amdahl - equipo {equipo}")
fig.tight_layout()
fig.savefig(f"docs/evidencias/graficas/ajuste_amdahl_{equipo}.png", dpi=110)
plt.close(fig)

tab = pd.DataFrame(filas)
tab.to_csv(f"{res}/ajuste_{equipo}.csv", index=False)
print("== Amdahl (escalabilidad fuerte) ==")
print(tab.drop(columns="equipo").to_string(index=False))

# Gustafson sobre la escalabilidad débil del Vigía, usando la f de Amdahl del Vigía
fv = float(tab[tab["caso"].str.startswith("Vigía")]["f_amdahl"].iloc[0])
db = db.sort_values("procs")
db["gustafson"] = db["procs"] - fv * (db["procs"] - 1)
fig, ax = plt.subplots(figsize=(5, 3.8))
ax.plot(db["procs"], db["escalado"], "o-", label="medido")
ax.plot(db["procs"], db["gustafson"], "s--", label=f"Gustafson f={fv:.3f}")
ax.plot(db["procs"], db["procs"], "k:", lw=1, label="ideal")
ax.set_xticks(list(db["procs"]))
ax.set_xlabel("procesos (simulaciones = base x p)")
ax.set_ylabel("speedup escalado")
ax.set_title(f"Gustafson, Vigía - equipo {equipo}")
ax.grid(alpha=0.3)
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(f"docs/evidencias/graficas/ajuste_gustafson_{equipo}.png", dpi=110)
plt.close(fig)
db[["equipo" if "equipo" in db else "modo", "procs", "nsims", "escalado", "gustafson"]].to_csv(
    f"{res}/ajuste_debil_{equipo}.csv", index=False)
print("\n== Gustafson (escalabilidad débil del Vigía) ==")
print(db[["procs", "nsims", "escalado", "gustafson"]].round(3).to_string(index=False))
print(f"\nAjustes en docs/evidencias/graficas/ y {res}/ para el equipo {equipo}")
