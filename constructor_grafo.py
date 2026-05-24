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

ARCHIVO_DATOS = os.path.join("datos", "papers_sistemas_distribuidos.json")
ARCHIVO_GRAFO = os.path.join("datos", "grafo_coautoria_sistemas_distribuidos.graphml")

def cargar_papers(ruta: str) -> list[dict]:
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)
        
def construir_grafo(papers: list[dict]) -> nx.Graph:
    G = nx.Graph()

    for paper in papers:
        autores = paper.get("authors", paper.get("autores", []))
        autores_ids = [a["authorId"] for a in autores if a.get("authorId")]

        # Agregar nodos para cada autor
        for autor in autores:
            if autor.get("authorId"):
                G.add_node(autor["authorId"], name=autor.get("name", "Desconocido"))

        # Agregar aristas para cada par de autores coescritos
        for a1, a2 in combinations(autores_ids, 2):
            if G.has_edge(a1, a2):
                G[a1][a2]["weight"] += 1
            else:
                G.add_edge(a1, a2, weight=1)

    return G

def main() -> nx.Graph:
    papers = cargar_papers(ARCHIVO_DATOS)
    grafo = construir_grafo(papers)
    nx.write_graphml(grafo, ARCHIVO_GRAFO)
    print(f"Grafo de coautoría construido y guardado en '{ARCHIVO_GRAFO}' con {grafo.number_of_nodes()} nodos y {grafo.number_of_edges()} aristas.")
    return grafo

if __name__ == "__main__":
    main()  