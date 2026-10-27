"""Consumo de API externa pública: Open-Meteo (previsão do tempo, gratuita e sem chave de acesso).

Relevância para o UrbanLink: o clima influencia a escolha do transporte. O programa busca a previsão
da cidade do usuário e sugere como ele pode se deslocar de forma sustentável e ganhar pontos.
"""
import requests

URL_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
URL_PREVISAO = "https://api.open-meteo.com/v1/forecast"
TEMPO_LIMITE = 10   # segundos


class ErroApi(Exception):
    """Falha ao consultar a API externa (sem internet, fora do ar, resposta inesperada)."""


def _consultar(url, parametros):
    try:
        resposta = requests.get(url, params=parametros, timeout=TEMPO_LIMITE)
        resposta.raise_for_status()
        return resposta.json()
    except requests.exceptions.Timeout as erro:
        raise ErroApi("A consulta demorou demais. Tente novamente.") from erro
    except requests.exceptions.ConnectionError as erro:
        raise ErroApi("Sem conexão com a internet.") from erro
    except requests.exceptions.HTTPError as erro:
        raise ErroApi(f"A API respondeu com erro: {erro}") from erro
    except ValueError as erro:
        raise ErroApi("A API devolveu uma resposta que não é JSON válido.") from erro


def buscar_cidade(nome):
    """Retorna {'nome', 'estado', 'pais', 'latitude', 'longitude'} ou None se a cidade não existir."""
    dados = _consultar(URL_GEOCODING, {"name": nome, "count": 1, "language": "pt", "format": "json"})
    resultados = dados.get("results")
    if not resultados:
        return None
    cidade = resultados[0]
    return {
        "nome": cidade["name"],
        "estado": cidade.get("admin1", ""),
        "pais": cidade.get("country", ""),
        "latitude": cidade["latitude"],
        "longitude": cidade["longitude"],
    }


def buscar_previsao(latitude, longitude):
    parametros = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto",
        "forecast_days": 1,
    }
    dados = _consultar(URL_PREVISAO, parametros)
    try:
        return {
            "temperatura_atual": dados["current"]["temperature_2m"],
            "codigo_clima": dados["current"]["weather_code"],
            "maxima": dados["daily"]["temperature_2m_max"][0],
            "minima": dados["daily"]["temperature_2m_min"][0],
            "chance_chuva": dados["daily"]["precipitation_probability_max"][0],
        }
    except (KeyError, IndexError, TypeError) as erro:
        raise ErroApi("A resposta da API veio em um formato inesperado.") from erro


def descrever_clima(codigo):
    """Traduz o código WMO devolvido pela API em texto."""
    if codigo == 0:
        return "Céu limpo"
    if codigo in (1, 2, 3):
        return "Parcialmente nublado"
    if codigo in (45, 48):
        return "Neblina"
    if 51 <= codigo <= 57:
        return "Garoa"
    if 61 <= codigo <= 67 or 80 <= codigo <= 82:
        return "Chuva"
    if 71 <= codigo <= 77 or codigo in (85, 86):
        return "Neve"
    if codigo >= 95:
        return "Tempestade"
    return "Condição variável"


def sugerir_deslocamento(previsao):
    """Regra simples que liga o clima ao tema do projeto (transporte público e sustentabilidade)."""
    chance = previsao["chance_chuva"] or 0
    if chance >= 60:
        return ("Alta chance de chuva: vá de transporte público e leve guarda-chuva. "
                "Use seus pontos para converter em bilhetes!")
    if previsao["maxima"] >= 30:
        return ("Dia quente: prefira metrô ou ônibus com ar-condicionado e leve água. "
                "Cada viagem evita CO2 e rende pontos.")
    return ("Tempo bom: que tal caminhar ou pedalar até a estação e seguir de transporte público? "
            "Bom dia para acumular pontos sustentáveis.")
