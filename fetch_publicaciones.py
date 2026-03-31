import pandas as pd
import requests
from bs4 import BeautifulSoup
import json

# CONFIGURACIÓN: Reemplaza con el ID de tu hoja de Google Sheets
SHEET_ID = "15RNq4EqnmyfRF4Fob1qkjqewGNViSi-u3merbRWWjCA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def extraer_metadatos(url):
    """Extrae título, autor, fecha y PDF de un repositorio tipo DSpace/Handle"""
    if not isinstance(url, str) or not url.startswith("http"):
        return None
        
    print(f"Extrayendo datos de: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        respuesta = requests.get(url.strip(), headers=headers, timeout=10)
        respuesta.raise_for_status()
        soup = BeautifulSoup(respuesta.text, 'html.parser')
        
        # Extracción de metadatos (etiquetas de Google Scholar / Dublin Core)
        titulo_tag = soup.find('meta', attrs={'name': 'citation_title'})
        titulo = titulo_tag['content'] if titulo_tag else 'Título no disponible'
        
        autores_tags = soup.find_all('meta', attrs={'name': 'citation_author'})
        autor = ", ".join([tag['content'] for tag in autores_tags]) if autores_tags else 'Autor no disponible'
        
        fecha_tag = soup.find('meta', attrs={'name': 'citation_date'})
        fecha = fecha_tag['content'] if fecha_tag else ''
        
        pdf_tag = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        pdf_url = pdf_tag['content'] if pdf_tag else url 
        
        return {
            "titulo": titulo,
            "autor": autor,
            "fecha": fecha,
            "url_pdf": pdf_url
        }
    except Exception as e:
        print(f"Error con {url}: {e}")
        return None

def main():
    print("Descargando datos de Google Sheets...")
    df = pd.read_csv(SHEET_URL)
    
    # Estructura del JSON final
    res = {
        "destacada": [],
        "ciencia": [],
        "otras": [],
        "externas": []
    }

    # Iteramos sobre las filas del Excel (Asumiendo Col 0: Categoria, Col 1: URL Repo, Col 2: URL Imagen)
    for index, row in df.iterrows():
        categoria = str(row.iloc[0]).strip()
        url_repo = str(row.iloc[1]).strip()
        url_img = str(row.iloc[2]).strip()
        
        if pd.isna(url_repo) or not url_repo.startswith("http"):
            continue
            
        metadatos = extraer_metadatos(url_repo)
        
        if metadatos:
            datos_completos = {
                "categoria": categoria,
                "url_repositorio": url_repo,
                "imagen": url_img,
                "titulo": metadatos["titulo"],
                "autor": metadatos["autor"],
                "fecha": metadatos["fecha"],
                "url": metadatos["url_pdf"] # Usamos el link directo al PDF si existe
            }
            
            # Clasificamos según la categoría escrita en el Excel
            cat_lower = categoria.lower()
            if "destacada" in cat_lower:
                res["destacada"].append(datos_completos)
            elif "ciencia" in cat_lower:
                res["ciencia"].append(datos_completos)
            elif "externas" in cat_lower:
                res["externas"].append(datos_completos)
            else:
                res["otras"].append(datos_completos)

    # Guardamos el archivo JSON local
    with open('publicaciones.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=4, ensure_ascii=False)
    
    print("¡Archivo publicaciones.json generado con éxito!")

if __name__ == "__main__":
    main()
