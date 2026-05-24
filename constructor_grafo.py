"""
Constructor del grafo de coautoría a partir de los datos recopilados mediante NetworkX.
Tema: Sistemas Distribuidos

Nodos: Autores (identificados por su authorId)
Aristas: Coautoría entre autores (si han coescrito al menos un paper juntos)
Peso: Numero de papers coescritos entre dos autores
"""

import json
import os  
import networkx as nx
from itertools import combinations

# Rutas de entrada y salida
ARCHIVO_DATOS = os.path.join("datos", "papers_sistemas_distribuidos.json")
ARCHIVO_GRAFO = os.path.join("datos", "grafo_coautoria_sistemas_distribuidos.graphml")


def cargar_papers(ruta: str) -> list[dict]:
    """Lee el archivo JSON y retorna la lista de papers."""
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def construir_grafo(papers: list[dict]) -> nx.Graph:
    """
    Construye el grafo de coautoría a partir de la lista de papers.

    Por cada paper:
      - Agrega un nodo por cada autor con su nombre como atributo.
      - Agrega una arista por cada par de autores que firmaron juntos. Si la arista ya existe, incrementa su peso en 1.

    Parámetros:
        papers: lista de diccionarios con los datos de cada paper

    Retorna:
        G: grafo no dirigido con nodos = autores y aristas = coautorías ponderadas
    """
    G = nx.Graph()

    for paper in papers:
        # Soporta tanto la clave "authors" como "autores" según el origen del JSON
        autores = paper.get("authors", paper.get("autores", []))

        # Filtra autores sin ID para evitar nodos sin identificador único
        autores_ids = [a["authorId"] for a in autores if a.get("authorId")]

        # Agrega un nodo por cada autor con su nombre como atributo
        for autor in autores:
            if autor.get("authorId"):
                G.add_node(autor["authorId"], name=autor.get("name", "Desconocido"))

        # Genera todos los pares posibles de autores del paper
        # Si ya existe la arista entre dos autores, incrementa el peso; si no, la crea con peso 1
        for a1, a2 in combinations(autores_ids, 2):
            if G.has_edge(a1, a2):
                G[a1][a2]["weight"] += 1
            else:
                G.add_edge(a1, a2, weight=1)

    return G


def main() -> nx.Graph:
    # Carga los papers, construye el grafo y lo serializa en formato GraphML
    papers = cargar_papers(ARCHIVO_DATOS)
    grafo = construir_grafo(papers)
    nx.write_graphml(grafo, ARCHIVO_GRAFO)
    print(f"Grafo de coautoría construido y guardado en '{ARCHIVO_GRAFO}' con {grafo.number_of_nodes()} nodos y {grafo.number_of_edges()} aristas.")
    return grafo

if __name__ == "__main__":
    main()  