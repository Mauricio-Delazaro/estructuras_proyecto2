"""
Visualización de la red de colaboración científica.
Área: Sistemas Distribuidos

Genera dos imágenes PNG:
  1. grafo_completo.png
  2. nodos_importantes.png

"""

import os
from collections import Counter
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from analisis_datos import load_graph, analizar_centralidad, analizar_comunidades, ARCHIVO_GRAFO

# Carpeta donde se guardan las imágenes generadas
DIR_SALIDA = "visualizaciones"


def grafo_componente_gigante(G):
    """Retorna el subgrafo formado únicamente por los nodos de la componente conexa más grande."""
    componente = max(nx.connected_components(G), key=len)
    return G.subgraph(componente).copy()


def visualizar_grafo_completo(G, mapa_comunidad):
    """
    Genera una imagen del grafo completo coloreando los nodos según su comunidad.
    Solo se destacan con color las 5 comunidades más grandes; el resto aparece en gris.

    Parámetros:
        G             : grafo completo de coautorías
        mapa_comunidad: dict {nodo: indice_comunidad} producido por analizar_comunidades()
    """
    print("Generando grafo completo...")

    # Cuenta cuántos nodos tiene cada comunidad y selecciona las 5 más grandes
    tam_comunidades = Counter(mapa_comunidad.values())
    top5_indices = {idx for idx, _ in tam_comunidades.most_common(5)}

    # Asigna un color distinto a cada una de las 5 comunidades
    _paleta = [plt.colormaps.get_cmap("tab10")(i) for i in range(5)]
    _paleta[3] = (1.0, 1.0, 0.0, 1.0)
    top5_color = {idx: _paleta[i] for i, idx in enumerate(sorted(top5_indices, key=tam_comunidades.get, reverse=True))}

    # Nodos sin ninguna arista (sin colaboraciones)
    aislados = {n for n, deg in G.degree() if deg == 0}

    # Determina el color de cada nodo según su categoría
    colores = []
    for node in G.nodes():
        comm = mapa_comunidad.get(node)
        if comm in top5_color:
            colores.append(top5_color[comm])        # pertenece a una de las top 5 comunidades
        elif node in aislados:
            colores.append((0.4, 0.4, 0.4, 1.0))    # autor sin colaboraciones
        else:
            colores.append((0.25, 0.25, 0.35, 1.0)) # comunidad pequeña (fuera del top 5)

    # Calcula la posición de cada nodo
    pos = nx.spring_layout(G, seed=42, k=0.6)

    fig, ax = plt.subplots(figsize=(18, 14))
    fig.patch.set_facecolor("#0f0f0f")
    ax.set_facecolor("#0f0f0f")

    # Calcula la transparencia de cada arista
    # Más colaboraciones = línea más visible
    pesos = [G[u][v]["weight"] for u, v in G.edges()]
    max_peso = max(pesos) if pesos else 1
    alphas = [0.05 + 0.95 * (w / max_peso) for w in pesos]

    # Dibuja cada arista como una línea entre las coordenadas de sus dos nodos
    for (u, v), alpha in zip(G.edges(), alphas):
        ax.plot(
            [pos[u][0], pos[v][0]],
            [pos[u][1], pos[v][1]],
            color="white",
            alpha=alpha,
            linewidth=0.5,
            zorder=1,
        )

    # Dibuja todos los nodos
    xs = [pos[n][0] for n in G.nodes()]
    ys = [pos[n][1] for n in G.nodes()]
    ax.scatter(xs, ys, c=colores, s=60, zorder=2, edgecolors="white", linewidths=0.3)

    # Construye la leyenda con las 5 comunidades más grandes y otras categorías adicionales
    top_comms = sorted(top5_color, key=tam_comunidades.get, reverse=True)
    parches = [
        mpatches.Patch(color=top5_color[idx], label=f"Comunidad {rank} ({tam_comunidades[idx]} autores)")
        for rank, idx in enumerate(top_comms, start=1)
    ]
    parches.append(mpatches.Patch(color=(0.25, 0.25, 0.35, 1.0), label="Otras comunidades"))
    parches.append(mpatches.Patch(color=(0.4, 0.4, 0.4, 1.0), label="Autores aislados"))
    ax.legend(handles=parches, loc="lower left", fontsize=8,
              facecolor="#1a1a1a", edgecolor="white", labelcolor="white")

    ax.set_title(
        f"Grafo completo\n"
        f"{G.number_of_nodes()} autores | {G.number_of_edges()} colaboraciones | {len(tam_comunidades)} comunidades",
        color="white", fontsize=13, pad=15,
    )
    ax.axis("off")

    os.makedirs(DIR_SALIDA, exist_ok=True)
    ruta = os.path.join(DIR_SALIDA, "grafo_completo.png")
    plt.savefig(ruta, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Guardado en: {ruta}")


def visualizar_nodos_importantes(G, centralidad, top_n=15):
    """
    Genera una imagen destacando los top n autores más influyentes según Degree Centrality.

    Parámetros:
        G          : grafo completo de coautorías
        centralidad: dict con métricas calculadas por analizar_centralidad()
        top_n      : cantidad de autores importantes a destacar
    """
    print("Generando nodos importantes...")

    # Trabaja solo sobre la componente gigante para que las métricas sean comparables
    Gc = grafo_componente_gigante(G)

    # Degree Centrality: proporción de nodos a los que está directamente conectado cada autor
    puntaje = {n: centralidad["degree"][n] for n in Gc.nodes() if n in centralidad["degree"]}

    # Selecciona los top n nodos con mayor puntaje
    top_nodes = sorted(puntaje, key=puntaje.get, reverse=True)[:top_n]
    top_set = set(top_nodes)

    pos = nx.spring_layout(Gc, seed=42, k=0.6)

    fig, ax = plt.subplots(figsize=(18, 14))
    fig.patch.set_facecolor("#0f0f0f")
    ax.set_facecolor("#0f0f0f")

    # Dibuja aristas: naranja si conectan al menos un nodo importante, blanco si no
    for u, v, data in Gc.edges(data=True):
        es_importante = u in top_set or v in top_set
        ax.plot(
            [pos[u][0], pos[v][0]],
            [pos[u][1], pos[v][1]],
            color="#f0a500" if es_importante else "white",
            alpha=0.6 if es_importante else 0.08,
            linewidth=1.2 if es_importante else 0.4,
            zorder=1,
        )

    # Dibuja nodos secundarios (no importantes) en gris
    nodos_normales = [n for n in Gc.nodes() if n not in top_set]
    xs = [pos[n][0] for n in nodos_normales]
    ys = [pos[n][1] for n in nodos_normales]
    ax.scatter(xs, ys, c="#4a4a6a", s=30, zorder=2, edgecolors="none")

    # Dibuja nodos importantes con tamaño y color proporcional a su puntaje
    sizes_top = [300 + puntaje[n] * 3000 for n in top_nodes]
    xs_top = [pos[n][0] for n in top_nodes]
    ys_top = [pos[n][1] for n in top_nodes]
    scatter = ax.scatter(
        xs_top, ys_top,
        c=[puntaje[n] for n in top_nodes],
        s=sizes_top,
        cmap="plasma",      # amarillo = mayor centralidad, azul = menor
        zorder=3,
        edgecolors="white",
        linewidths=0.8,
    )

    # Etiqueta cada nodo importante con el nombre del autor
    for node in top_nodes:
        name = Gc.nodes[node].get("name", node)
        label = name if len(name) <= 20 else name[:18] + "…"
        ax.annotate(
            label,
            xy=pos[node],
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=7,
            color="white",
            zorder=4,
        )

    # Barra lateral que indica el valor de Degree Centrality
    plt.colorbar(scatter, ax=ax, label="Degree Centrality", shrink=0.6)

    ax.set_title(
        f"Nodos importantes (Degree Centrality)\n",
        color="white", fontsize=13, pad=15,
    )
    ax.axis("off")

    ruta = os.path.join(DIR_SALIDA, "nodos_importantes.png")
    plt.savefig(ruta, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Guardado en: {ruta}")


def main():
    # Cargar el grafo
    print("Cargando grafo...")
    G = load_graph(ARCHIVO_GRAFO)
    print(f"  {G.number_of_nodes()} nodos | {G.number_of_edges()} aristas")

    centralidad = analizar_centralidad(G)
    mapa_comunidad = analizar_comunidades(G)

    visualizar_grafo_completo(G, mapa_comunidad)
    visualizar_nodos_importantes(G, centralidad, top_n=15)

    print("\nVisualizaciones generadas en 'visualizaciones/'.")


if __name__ == "__main__":
    main()
