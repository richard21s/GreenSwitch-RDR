import logging
import re
import requests
import streamlit as st

logging.basicConfig(level=logging.INFO)

# --- Compatibility Helpers for older Streamlit versions ---
def safe_cache_data(*args, **kwargs):
    if hasattr(st, "cache_data"):
        return st.cache_data(*args, **kwargs)
    return st.experimental_memo(*args, **kwargs)


@safe_cache_data(ttl=3600)  # Cache selama 1 jam (Kompatibel dengan Streamlit lama & modern)
def get_bbm_price(jenis_bbm="Pertalite"):
    """
    Scrapes the current BBM price dynamically from the MyPertamina API.
    Falls back to a default value if the API call fails.
    """
    default_prices = {
        "Pertalite": 10000,
        "Pertamax": 12950,
        "Pertamax Turbo": 14400
    }
    default_price = default_prices.get(jenis_bbm, 10000)
    
    url = "https://api.web.mypertamina.id/price"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        logging.info(f"Mengambil harga BBM terupdate dari API MyPertamina...")
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get("data", {}).get("data", [])
            
            # Cari Prov. DKI Jakarta
            for item in items:
                prov = item.get("province", "")
                if "dki jakarta" in prov.lower() or "jakarta" in prov.lower():
                    list_price = item.get("list_price", [])
                    # Cari produk yang sesuai
                    for price_item in list_price:
                        product_name = price_item.get("product", "").upper()
                        if jenis_bbm.upper() in product_name:
                            price_str = str(price_item.get("price", ""))
                            # Ekstrak angka saja (misal: "Rp 10.000" atau "12300")
                            match = re.search(r'(\d{2,3}[\.,]\d{3}|\d+)', price_str)
                            if match:
                                val = match.group(1).replace('.', '').replace(',', '')
                                logging.info(f"Berhasil mengambil harga BBM {jenis_bbm} dari API: Rp {val}")
                                return int(val)
                                
        logging.warning(f"Gagal mengambil harga BBM dinamis dari API MyPertamina. Menggunakan harga default {jenis_bbm}: Rp {default_price:,}")
        return default_price
        
    except Exception as e:
        logging.warning(f"Gagal memanggil API MyPertamina: {e}. Menggunakan harga default {jenis_bbm}: Rp {default_price:,}")
        return default_price

def get_pln_tariffs():
    """
    Menyediakan data Tarif Dasar Listrik (TDL) PLN.
    Sebagai prototipe lomba, data ini di-hardcode untuk menjamin stabilitas dan kecepatan, 
    mengingat TDL jarang berubah dan scraping dari PDF sangat membebani komputasi.
    """
    return [
        {"label": "R-1 / 900 VA", "tarif": 1352},
        {"label": "R-1 / 1300 VA", "tarif": 1444},
        {"label": "R-2 / 2200 VA", "tarif": 1444},
        {"label": "R-3 / 3500+ VA", "tarif": 1699},
    ]

def get_ev_database():
    """
    Menyediakan database Kendaraan Listrik (EV).
    Di-hardcode demi stabilitas demo lomba, karena scraping dari banyak website pabrikan 
    (Wuling, Hyundai, dll) berisiko tinggi terkena blokir (anti-bot) atau timeout saat live demo.
    """
    return [
        {"nama": "Smoot Tempur", "harga": 20, "jangkauan": 60, "tipe": "motor", "charging": "Swap Baterai", "catatan": "Pilihan paling ekonomis dengan sistem baterai swap."},
        {"nama": "Gesits G1", "harga": 28, "jangkauan": 50, "tipe": "motor", "charging": "3-4 Jam", "catatan": "Produk dalam negeri dengan jaringan servis yang mulai berkembang."},
        {"nama": "ALVA One", "harga": 36, "jangkauan": 70, "tipe": "motor", "charging": "4 Jam", "catatan": "Motor listrik lokal dengan desain modern untuk commuter harian."},
        {"nama": "Wuling Air EV Lite", "harga": 190, "jangkauan": 200, "tipe": "mobil_kecil", "charging": "8.5 Jam", "catatan": "Sangat compact untuk mobilitas perkotaan padat."},
        {"nama": "Wuling Binguo EV", "harga": 317, "jangkauan": 333, "tipe": "mobil_kecil", "charging": "DC Fast 35 Min", "catatan": "Desain retro klasik dengan ruang kabin yang cukup lega."},
        {"nama": "BYD Dolphin", "harga": 425, "jangkauan": 410, "tipe": "mobil_besar", "charging": "DC Fast 30 Min", "catatan": "Hatchback bertenaga dengan teknologi Blade Battery yang aman."},
        {"nama": "Hyundai Ioniq 5", "harga": 782, "jangkauan": 384, "tipe": "mobil_besar", "charging": "DC Fast 18 Min", "catatan": "Platform EV murni dengan fitur V2L untuk listrik rumah tangga."},
    ]
