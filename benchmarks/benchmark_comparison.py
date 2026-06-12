import time
import pandas as pd
import polars as pl

FICHIER = "data/lst_of_users_anon_2.csv"
COLONNES = ["DATE_CREATION", "DATE_DESACTIVATION", "DATE_DERNIERE_CONNECTION_1"]

print("=" * 55)
print("BENCHMARK Pandas vs Polars")
print(f"Fichier : {FICHIER} (182 MB, 2.1M lignes)")
print("=" * 55)

# ─── PANDAS ────────────────────────────────────────────
print("\n[PANDAS] Traitement en cours...")
start = time.time()

df_pd = pd.read_csv(FICHIER, sep=";")
for col in COLONNES:
    # Pandas : conversion de dates (mono-thread)
    df_pd[col] = pd.to_datetime(df_pd[col], format="%m/%d/%Y", errors="coerce")
    df_pd[col] = df_pd[col].dt.strftime("%d-%m-%Y %H:%M:%S")

temps_pandas = time.time() - start
print(f"[PANDAS] Terminé en {temps_pandas:.2f}s")

# ─── POLARS ────────────────────────────────────────────
print("\n[POLARS] Traitement en cours...")
start = time.time()

df_pl = pl.read_csv(FICHIER, separator=";")
for col in COLONNES:
    df_pl = df_pl.with_columns(
        pl.col(col)
        .str.to_datetime(format="%m/%d/%Y", strict=False)
        .dt.strftime("%d-%m-%Y %H:%M:%S")
        .alias(col)
    )

temps_polars = time.time() - start
print(f"[POLARS] Terminé en {temps_polars:.2f}s")

# ─── RÉSULTAT ──────────────────────────────────────────
print("\n" + "=" * 55)
print("RÉSULTATS")
print("=" * 55)
print(f"Pandas : {temps_pandas:.2f}s")
print(f"Polars : {temps_polars:.2f}s")
if temps_polars > 0:
    print(f"Polars est {temps_pandas / temps_polars:.1f}x plus rapide")