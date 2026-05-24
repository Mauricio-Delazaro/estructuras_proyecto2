"""
Análisis de la red de colaboración científica.
Área: Sistemas Distribuidos

Incluye:
  a) Caminos mínimos (Dijkstra)
  b) Centralidad (Degree, Betweenness, Closeness)
  c) Componentes conexas
  d) Detección de comunidades
"""

import os
import networkx as nx
from networkx.algorithms import community as nx_community

ARCHIVO_GRAFO = os.path.join("datos", "grafo_coautoria_sistemas_distribuidos.graphml")

def load_graph(path):
    G = nx.read_graphml(path)
    # Normalizar pesos 
    for node_a, node_b, edge_data in G.edges(data=True):
        try:
            edge_data['weight'] = float(edge_data.get('weight', 1.0))
        except Exception:
            edge_data['weight'] = 1.0
    return G


# a) CAMINOS MÍNIMOS
def analizar_caminos(G, top_k_pairs=3):
    print(f"\n{'='*55}")
    print("  a) CAMINOS MINIMOS")
    print(f"{'='*55}")

    # seleccionar hasta top_k_pairs aristas por weight
    edges = sorted(G.edges(data=True), key=lambda e: float(e[2].get("weight", 0)), reverse=True)[:top_k_pairs]
    if not edges:
        print("  No hay aristas en el grafo.")
        return []

    resultados = []

    # preparar atributo inverso para Dijkstra: mayor weight -> menor distancia
    for author_a, author_b, edge_data in G.edges(data=True):
        weight_value = float(edge_data.get("weight", 1))
        edge_data["inv_weight"] = 1.0 / weight_value if weight_value != 0 else float('inf')

    for idx, (author_a, author_b, edge_info) in enumerate(edges, start=1):
        name_a = G.nodes[author_a].get("name", author_a)
        name_b = G.nodes[author_b].get("name", author_b)
        print(f"\n  Pareja {idx}: {name_a} ({author_a}) <-> {name_b} ({author_b}), colaboraciones={int(edge_info.get('weight',0))}")
        if not nx.has_path(G, author_a, author_b):
            print("    No hay camino entre los autores seleccionados.")
            resultados.append({"pareja": (author_a, author_b), "dijkstra": None})
            continue
        # Dijkstra sobre inv_weight
        path_d = nx.dijkstra_path(G, author_a, author_b, weight="inv_weight")
        dist_d = nx.dijkstra_path_length(G, author_a, author_b, weight="inv_weight")
        print(f"    [Dijkstra] Distancia ponderada: {dist_d:.4f} | Saltos: {len(path_d)-1}")
        print("    Ruta:")
        for node_id in path_d:
            print(f"      -> {G.nodes[node_id].get('name', node_id)}")
        resultados.append({"pareja": (author_a, author_b), "dijkstra": {"ruta": path_d, "valor": dist_d}})

    # limpiar atributo temporal
    for _, _, edge_data in G.edges(data=True):
        if "inv_weight" in edge_data:
            del edge_data["inv_weight"]

    # diametro y radio de la componente gigante
    try:
        giant_nodes = max(nx.connected_components(G), key=len)
        giant_subgraph = G.subgraph(giant_nodes)
        print(f"\n  Diametro de la componente gigante : {nx.diameter(giant_subgraph)}")
        print(f"  Radio de la componente gigante    : {nx.radius(giant_subgraph)}")
    except Exception:
        pass
    return resultados


# b) CENTRALIDAD
def analizar_centralidad(G):
    print(f"\n{'='*55}")
    print("  b) CENTRALIDAD")
    print(f"{'='*55}")

    # Calcular degree centrality (no ponderada)
    degree_cent = nx.degree_centrality(G)
    # Calcular betweenness y closeness usando el peso inverso para reflejar la fuerza de colaboración 
    # (Más peso = más colaboración = menor distancia)
    for node_a, node_b, edge_data in G.edges(data=True):
        try:
            w = float(edge_data.get('weight', 1.0))
        except Exception:
            w = 1.0
        edge_data['inv_weight'] = 1.0 / w if w > 0 else float('inf')

    peso = 'inv_weight'
    betweenness_cent = nx.betweenness_centrality(G, weight=peso)
    closeness_cent = nx.closeness_centrality(G, distance=peso)

    # Limpiar atributo temporal
    for _, _, edge_data in G.edges(data=True):
        if 'inv_weight' in edge_data:
            del edge_data['inv_weight']

    def top5(metrica, label):
        ranking = sorted(metrica.items(), key=lambda item: item[1], reverse=True)[:5]
        print(f"\n  Top 5 - {label}:")
        for idx, (node_id, val) in enumerate(ranking, 1):
            name = G.nodes[node_id].get("name", node_id)
            print(f"    {idx}. {name} ({val:.4f})")

    top5(degree_cent, "Degree Centrality")
    top5(betweenness_cent, "Betweenness Centrality")
    top5(closeness_cent, "Closeness Centrality")

    return {"degree": degree_cent, "betweenness": betweenness_cent, "closeness": closeness_cent}


# c) COMPONENTES CONEXAS
def analizar_componentes(G):
    print(f"\n{'='*55}")
    print("  c) COMPONENTES CONEXAS")
    print(f"{'='*55}")

    components = sorted(nx.connected_components(G), key=len, reverse=True)
    aislados = [node_id for node_id, deg in G.degree() if deg == 0]

    print(f"\n  Total de componentes  : {len(components)}")
    print(f"  Autores aislados      : {len(aislados)}")
    if components:
        print(f"  Componente gigante    : {len(components[0])} nodos")
    print(f"\n  Tamano de las 10 componentes mas grandes:")
    for idx, comp in enumerate(components[:10], 1):
        print(f"    {idx}. {len(comp)} nodos")
    if components:
        print(f"\n  Autores en la componente gigante (muestra de 5):")
        for node_id in list(components[0])[:5]:
            print(f"    - {G.nodes[node_id].get('name', node_id)}")

    return {"components": components, "isolates": aislados}


# d) DETECCIÓN DE COMUNIDADES 
def analizar_comunidades(G):
    print(f"\n{'='*55}")
    print("  d) DETECCION DE COMUNIDADES")
    print(f"{'='*55}")

    
    comms = list(nx_community.greedy_modularity_communities(G, weight="weight"))
    mapa = {}
    for idx, community in enumerate(comms):
        for node_id in community:
            mapa[node_id] = idx
    mod = nx_community.modularity(G, comms, weight="weight")
    print(f"\n  Comunidades detectadas: {len(comms)}")
    print(f"  Modularidad: {mod:.4f}")
    for idx, community in enumerate(sorted(comms, key=len, reverse=True)[:5], 1):
        nombres = [G.nodes[node_id].get('name', node_id) for node_id in list(community)[:3]]
        print(f"    Comunidad {idx} - {len(community)} autores | Ej: {', '.join(nombres)}...")
    return mapa


# MAIN
def main():
    print("Cargando grafo...")
    G = load_graph(ARCHIVO_GRAFO)
    print(f"  {G.number_of_nodes()} nodos | {G.number_of_edges()} aristas")

    caminos = analizar_caminos(G, top_k_pairs=3)
    centralidad = analizar_centralidad(G)
    comp_info = analizar_componentes(G)
    particion = analizar_comunidades(G)

    print(f"\n{'='*55}")
    print("  Analisis completado.")
    print(f"{'='*55}\n")

    return G, centralidad, particion


if __name__ == "__main__":
    main()
