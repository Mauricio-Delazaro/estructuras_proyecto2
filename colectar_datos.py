"""
Recolección de datos de la API de Semantic Scholar.
Tema: Sistemas Distribuidos

Consulta la API, filtra los papers válidos y los guarda en un archivo JSON
para ser usado posteriormente por constructor_grafo.py.
"""

import requests
import json
import time
import os

# URL base de la API de Semantic Scholar
API_URL = "https://api.semanticscholar.org/graph/v1/"

# Carpeta y archivo de salida donde se guardan los papers recolectados
DIR_DATOS = "datos"
OUTPUT_FILE = os.path.join(DIR_DATOS, "papers_sistemas_distribuidos.json")

# Lista de términos de búsqueda — se puede ampliar para cubrir más áreas
QUERIES = [
    "Sistemas distribuidos",
]


def obtener_datos(query: str, limite: int = 100, offset: int = 0) -> dict:
    """
    Realiza una solicitud a la API de Semantic Scholar y retorna los resultados.

    Si la API responde con código 429 (límite de solicitudes alcanzado),
    espera 45 segundos y reintenta automáticamente.

    Parámetros:
        query  : término de búsqueda
        limite : cantidad máxima de resultados por solicitud
        offset : desplazamiento para paginar resultados

    Retorna:
        diccionario con los datos de la respuesta, o vacío si hubo un error
    """
    url = f"{API_URL}paper/search"
    params = {
        "query": query,
        "fields": "paperId,title,authors,year",
        "limit": limite,
        "offset": offset,
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            # La API limita la cantidad de solicitudes por minuto
            print("Límite alcanzado. Esperando para reintentar...")
            time.sleep(45)
            return obtener_datos(query, limite, offset)
        else:
            print(f"Error en la solicitud: {response.status_code} - {response.text}")
            return {}
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud: {e}")
        return {}


def procesar_datos() -> list[dict]:
    """
    Ejecuta todas las queries, filtra los papers válidos y guarda el resultado en JSON.

    Un paper es válido si tiene: paperId, año de publicación y al menos un autor con ID.
    Los papers duplicados se descartan usando el paperId como clave única.

    Retorna:
        lista de diccionarios con los datos de cada paper recolectado
    """
    os.makedirs(DIR_DATOS, exist_ok=True)

    # Usa un diccionario indexado por paperId para evitar duplicados entre queries
    all_papers: dict[str, dict] = {}

    for query in QUERIES:
        print(f"Obteniendo datos para la query: '{query}'")
        offset = 0

        while len(all_papers) < 100:
            resultados = obtener_datos(query, limite=100, offset=offset)

            if not resultados or "data" not in resultados:
                print("  -> Sin resultados.")
                break

            nuevos = 0
            for paper in resultados["data"]:
                pid = paper.get("paperId")
                authors = paper.get("authors", [])
                year = paper.get("year")

                # Filtra autores sin ID para garantizar nodos identificables en el grafo
                autores_validos = [a for a in authors if a.get("authorId")]

                if pid and pid not in all_papers and len(autores_validos) >= 1 and year:
                    all_papers[pid] = {
                        "paperId": pid,
                        "title": paper.get("title", "Sin título"),
                        "authors": [
                            {"authorId": a["authorId"], "name": a.get("name", "Desconocido")}
                            for a in autores_validos
                        ],
                        "year": year,
                    }
                    nuevos += 1

            print(f"  -> {nuevos} papers nuevos. Total acumulado: {len(all_papers)}")

            # Pausa para respetar el rate limit de la API (máximo de solicitudes por segundo)
            time.sleep(1.5)

            offset += len(resultados["data"])

            if not resultados["data"] or len(all_papers) >= 100:
                break

    papers_lista = list(all_papers.values())

    # Verifica que se hayan recolectado al menos 100 autores únicos
    author_ids = {
        a["authorId"]
        for paper in papers_lista
        for a in paper["authors"]
        if a.get("authorId")
    }

    print(f"Autores únicos encontrados: {len(author_ids)}")

    if len(author_ids) >= 100:
        print("Se han agregado al menos 100 autores únicos al diccionario.")
    else:
        print("Aún no se han agregado 100 autores únicos al diccionario.")

    # Serializa los papers en formato JSON con indentación legible
    with open(OUTPUT_FILE, "w", encoding="utf-8") as archivo:
        json.dump(papers_lista, archivo, ensure_ascii=False, indent=2)

    return papers_lista


if __name__ == "__main__":
    procesar_datos()
