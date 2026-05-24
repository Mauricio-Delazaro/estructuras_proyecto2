"""
Recolección de datos de la API de Semantic Scholar
Tema: Sistemas distribuidos
"""

"Imports para la recolección de datos, procesamiento y almacenamiento"
import requests
import json    
import time
import os

API_URL = "https://api.semanticscholar.org/graph/v1/"
DIR_DATOS = "datos"
OUTPUT_FILE = os.path.join(DIR_DATOS, "papers_sistemas_distribuidos.json")

"Lista de queries (posible agregar mas de una query para obtener datos en diferentes idiomas/areas relacionadas)"
QUERIES = [
    "Sistemas distribuidos",
]

"Función para hacer request de la API de Semantic Scholar"

def obtener_datos(query: str, limite: int = 100, offset: int = 0) -> dict:
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
            print("Límite alcanzado. Esperando para reintentar...")
            time.sleep(45)  # Esperar 45 segundos antes de reintentar
            return obtener_datos(query, limite, offset)  # Reintenta la solicitud
        else:
            print(f"Error en la solicitud: {response.status_code} - {response.text}")
            return {}
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud: {e}")
        return {}
    
"Función para realizar multiples queries y guardar los datos en un archivo JSON"

def procesar_datos() -> list[dict]:
    os.makedirs(DIR_DATOS, exist_ok=True)
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

                # Tiene que haber al menos 1 autor valido
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

            # Pausa para respetar el rate limit de la API
            time.sleep(1.5)

            offset += len(resultados["data"])

            if not resultados["data"] or len(all_papers) >= 100:
                break

    papers_lista = list(all_papers.values())

    # Conteo de autores únicos para verificar el mínimo de 100
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

    with open(OUTPUT_FILE, "w", encoding="utf-8") as archivo:
        json.dump(papers_lista, archivo, ensure_ascii=False, indent=2)

    return papers_lista


if __name__ == "__main__":
    procesar_datos()
