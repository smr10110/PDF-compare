"""Módulo de cálculo de similitud temática entre conjuntos de keywords."""


def similitud_jaccard(set_a: set, set_b: set) -> float:
    """Calcula el índice de Jaccard entre dos conjuntos, expresado en porcentaje.

    El índice de Jaccard mide la proporción de elementos comunes respecto
    al total de elementos únicos en la unión de ambos conjuntos.

    Args:
        set_a: Primer conjunto de keywords.
        set_b: Segundo conjunto de keywords.

    Returns:
        Porcentaje de similitud entre 0.0 y 100.0.
    """
    if not set_a and not set_b:
        return 0.0
    interseccion = set_a & set_b
    union = set_a | set_b
    return len(interseccion) / len(union) * 100


def etiqueta_similitud(pct: float) -> str:
    """Convierte un porcentaje de similitud en una etiqueta cualitativa.

    Args:
        pct: Porcentaje de similitud (0–100).

    Returns:
        Etiqueta descriptiva del nivel de relación temática.
    """
    if pct >= 60:
        return "Altamente relacionados"
    if pct >= 30:
        return "Medianamente relacionados"
    if pct >= 10:
        return "Muy poco relacionados"
    return "No relacionados"


def comparar_conjuntos(lista_keywords: list[list[str]]) -> dict:
    """Compara múltiples listas de keywords y calcula sus métricas de similitud.

    Funciona tanto para 2 documentos (caso más común) como para 3 o más.
    En el caso de 2 documentos calcula las keywords exclusivas de cada uno;
    para más documentos usa la intersección global.

    Args:
        lista_keywords: Lista de listas, una por documento. Cada lista
                        contiene las keywords extraídas de ese documento.

    Returns:
        Diccionario con las claves:
            - intersection: keywords presentes en todos los documentos.
            - only_a: keywords exclusivas del primer documento.
            - only_b: keywords exclusivas del segundo documento.
            - sim_pct: porcentaje de similitud redondeado a 1 decimal.
            - label: etiqueta cualitativa de la similitud.
    """
    conjuntos = [set(kws) for kws in lista_keywords]

    pairwise = {}

    if len(conjuntos) == 2:
        interseccion = conjuntos[0] & conjuntos[1]
        only_a = conjuntos[0] - conjuntos[1]
        only_b = conjuntos[1] - conjuntos[0]
        only_c = set()
        sim_pct = similitud_jaccard(conjuntos[0], conjuntos[1])
    else:
        # Intersecciones por pares
        int_ab = conjuntos[0] & conjuntos[1]
        int_ac = conjuntos[0] & conjuntos[2]
        int_bc = conjuntos[1] & conjuntos[2]
        interseccion = int_ab & conjuntos[2]  # común a los 3

        # Similitud global = promedio de los 3 pares (captura relaciones parciales)
        sim_ab = similitud_jaccard(conjuntos[0], conjuntos[1])
        sim_ac = similitud_jaccard(conjuntos[0], conjuntos[2])
        sim_bc = similitud_jaccard(conjuntos[1], conjuntos[2])
        sim_pct = (sim_ab + sim_ac + sim_bc) / 3

        # Keywords exclusivas de cada documento
        only_a = conjuntos[0] - conjuntos[1] - conjuntos[2]
        only_b = conjuntos[1] - conjuntos[0] - conjuntos[2]
        only_c = conjuntos[2] - conjuntos[0] - conjuntos[1]

        pairwise = {
            "ab": round(sim_ab, 1),
            "ac": round(sim_ac, 1),
            "bc": round(sim_bc, 1),
            "int_ab": len(int_ab),
            "int_ac": len(int_ac),
            "int_bc": len(int_bc),
        }

    return {
        "intersection": list(interseccion),
        "only_a": list(only_a)[:50],
        "only_b": list(only_b)[:50],
        "only_c": list(only_c)[:50],
        "pairwise": pairwise,
        "sim_pct": round(sim_pct, 1),
        "label": etiqueta_similitud(sim_pct),
    }
