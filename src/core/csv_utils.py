# Séparateurs candidats, par ordre de probabilité
SEPARATEURS_POSSIBLES = [";", ",", "\t", "|"]


def detecter_separateur(chemin_fichier: str) -> str:
    """
    Détecte le séparateur d'un fichier CSV en analysant sa première ligne.
    On compte les occurrences de chaque séparateur candidat dans l'en-tête,
    et on retourne le plus fréquent.

    chemin_fichier : chemin local du fichier (ex: /tmp/input.csv)
    """
    # Lire uniquement la première ligne (l'en-tête)
    with open(chemin_fichier, "r", encoding="utf-8", errors="ignore") as f:
        premiere_ligne = f.readline()

    # Compter chaque séparateur candidat
    comptes = {sep: premiere_ligne.count(sep) for sep in SEPARATEURS_POSSIBLES}

    # Trouver le séparateur le plus fréquent
    separateur = max(comptes, key=comptes.get)

    # Si aucun séparateur trouvé, défaut sur la virgule
    if comptes[separateur] == 0:
        return ","

    return separateur