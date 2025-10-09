import requests
from bs4 import BeautifulSoup

def extraer_ficha_tecnica(url):
    # Obtener el contenido HTML de la página
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # Analizar el HTML con BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Buscar la sección de ficha técnica
    ficha = soup.find('section', {'id': 'technicalData'})
    if ficha is None:
        return None  # No existe la sección

    # Extraer los datos
    datos = {}
    for p in ficha.find_all('p', class_='m-none'):
        nombre_tag = p.find('small')
        valor_tag = p.find('span')

        if nombre_tag and valor_tag:
            clave = nombre_tag.get_text(strip=True)
            valor = valor_tag.get_text(strip=True)
            datos[clave] = valor

    return datos

# 🔍 Ejemplo con tu URL
url = "https://ecuador.patiotuerca.com/vehicle/autos-nissan-qashqai_sense-quito-2020/1925036"
ficha = extraer_ficha_tecnica(url)

print(ficha)