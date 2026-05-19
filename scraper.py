import logging
import re
from playwright.sync_api import sync_playwright
import streamlit as st

logging.basicConfig(level=logging.INFO)

@st.experimental_memo(ttl=3600)  # Cache selama 1 jam (Kompatibel dengan Streamlit lama)
def get_bbm_price(jenis_bbm="Pertalite"):
    """
    Scrapes the current BBM price dynamically from MyPertamina using Playwright.
    Falls back to a default value if scraping fails.
    """
    default_prices = {
        "Pertalite": 10000,
        "Pertamax": 12950,
        "Pertamax Turbo": 14400
    }
    default_price = default_prices.get(jenis_bbm, 10000)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            url = "https://mypertamina.id/about/product-price"
            
            logging.info(f"Membuka {url} dengan Playwright...")
            page.goto(url, timeout=30000)
            
            row_selector = "table tr:has-text('Prov. DKI Jakarta')"
            page.wait_for_selector(row_selector, timeout=15000)
            
            col_idx = 2
            if jenis_bbm.lower() == "pertamax":
                col_idx = 3
            elif jenis_bbm.lower() == "pertamax turbo":
                col_idx = 4
                
            price_text = page.locator(f"{row_selector} td:nth-child({col_idx})").first.inner_text()
            
            if price_text:
                match = re.search(r'(\d{2,3}[\.,]\d{3})', price_text)
                if match:
                    price_str = match.group(1).replace('.', '').replace(',', '')
                    logging.info(f"Berhasil scrape harga {jenis_bbm}: Rp {price_str}")
                    browser.close()
                    return int(price_str)
            
            logging.info(f"Gagal memparsing angka dari teks: {price_text}")
            browser.close()
            return default_price
            
    except Exception as e:
        logging.error(f"Gagal melakukan scraping harga BBM dengan Playwright: {e}")
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
