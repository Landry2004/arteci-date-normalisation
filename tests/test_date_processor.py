import polars as pl
from src.core.date_processor import normalize_column


def _normaliser(valeurs: list, primary_format: str) -> list:
    """Helper : normalise une colonne et retourne la liste des résultats."""
    df = pl.DataFrame({"date": valeurs})
    df = normalize_column(df, "date", primary_format)
    return df["date"].to_list()


def test_format_dmy_simple():
    # Date française classique
    resultat = _normaliser(["15/03/2024"], "DMY")
    assert resultat[0] == "15-03-2024 00:00:00"


def test_format_mdy_simple():
    # Date américaine classique
    resultat = _normaliser(["03/15/2024"], "MDY")
    assert resultat[0] == "15-03-2024 00:00:00"


def test_format_mixte_bascule_mdy():
    # Colonne DMY mais date impossible en DMY (mois 15) -> bascule MDY
    resultat = _normaliser(["03/15/2024"], "DMY")
    assert resultat[0] == "15-03-2024 00:00:00"


def test_format_mixte_dans_meme_colonne():
    # Une ligne DMY, une ligne MDY dans la même colonne
    resultat = _normaliser(["14/02/2026", "02/28/2026"], "DMY")
    assert resultat[0] == "14-02-2026 00:00:00"
    assert resultat[1] == "28-02-2026 00:00:00"


def test_format_iso():
    resultat = _normaliser(["2024-03-15"], "DMY")
    assert resultat[0] == "15-03-2024 00:00:00"


def test_cellule_invalide_gardee():
    # Texte non parsable -> gardé tel quel
    resultat = _normaliser(["texte_invalide"], "DMY")
    assert resultat[0] == "texte_invalide"


def test_cellule_vide_preservee():
    # Valeur vide -> reste null
    resultat = _normaliser([None], "DMY")
    assert resultat[0] is None


def test_colonne_complete():
    # Cas réaliste mélangeant tous les cas
    valeurs = ["15/03/2024", "03/15/2024", "texte", None]
    resultat = _normaliser(valeurs, "DMY")
    assert resultat[0] == "15-03-2024 00:00:00"
    assert resultat[1] == "15-03-2024 00:00:00"
    assert resultat[2] == "texte"
    assert resultat[3] is None