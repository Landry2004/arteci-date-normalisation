import polars as pl

# Format de sortie standard demandé par le cahier des charges
OUTPUT_FORMAT = "%d-%m-%Y %H:%M:%S"

# Formats français 
FORMATS_DMY = [
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y",
    "%d-%m-%Y %H:%M:%S",
    "%d-%m-%Y",
]

# Formats anglais 
FORMATS_MDY = [
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y",
    "%m-%d-%Y %H:%M:%S",
    "%m-%d-%Y",
]

# Format ISO (année en premier)
FORMATS_ISO = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
]


def _build_parse_expression(column: str, primary_format: str) -> pl.Expr:
    # Ordre des essais : format principal, puis inverse, puis ISO
    if primary_format.upper() == "DMY":
        formats_ordonnes = FORMATS_DMY + FORMATS_MDY + FORMATS_ISO
    else:
        formats_ordonnes = FORMATS_MDY + FORMATS_DMY + FORMATS_ISO

    col = pl.col(column).cast(pl.Utf8).str.strip_chars()
    parsed = col.str.to_datetime(format=formats_ordonnes[0], strict=False, exact=True)

    # Pour chaque date non parsée (null), on tente le format suivant
    for fmt in formats_ordonnes[1:]:
        parsed = parsed.fill_null(
            col.str.to_datetime(format=fmt, strict=False, exact=True)
        )

    return parsed


def normalize_column(df: pl.DataFrame, column: str, primary_format: str) -> pl.DataFrame:
    # Sauvegarde de la valeur originale (pour les cellules non parsables)
    original = pl.col(column).cast(pl.Utf8)
    parsed = _build_parse_expression(column, primary_format)

    # Si parsé → format standard, sinon → valeur originale gardée telle quelle
    resultat = (
        pl.when(parsed.is_not_null())
        .then(parsed.dt.strftime(OUTPUT_FORMAT))
        .otherwise(original)
        .alias(column)
    )

    return df.with_columns(resultat)