# 🍃 GreenSwitch — AI Agent Transisi Energi ⚡

GreenSwitch adalah asisten cerdas (AI Agent) interaktif berbasis web yang membantu pengguna untuk menganalisis kelayakan finansial dan dampak lingkungan dari transisi kendaraan berbahan bakar minyak (BBM) menuju Kendaraan Listrik (Electric Vehicle / EV). Aplikasi ini menggunakan data *real-time* harga BBM dan Listrik, serta penalaran dari AI untuk memberikan laporan keputusan transisi yang sangat presisi dan dipersonalisasi.

---

## 1. Arsitektur Sistem & Teknologi

GreenSwitch dibangun menggunakan perpaduan teknologi web interaktif dan *Large Language Models* mutakhir:
*   **Frontend & Web Framework:** [Streamlit](https://streamlit.io/) (Python). Digunakan karena kemampuannya membangun UI data reaktif secara cepat. Antarmuka telah dimodifikasi secara ekstensif dengan injeksi *Custom CSS* (Tailwind-style) dan JavaScript untuk menghadirkan desain modern (*glassmorphism*, *smooth scrolling*, dan UI/UX yang dinamis).
*   **LLM Engine (Brain):** **Google Gemini 2.0 Flash / Pro** (melalui integrasi `google-genai`). Bertindak sebagai *Large Language Model* (LLM) utama yang menjadi mesin *Agent Reasoning* untuk memproses bahasa alami, melakukan kalkulasi penghematan biaya dan *Return of Investment* (ROI), serta merumuskan rekomendasi EV spesifik secara terstruktur sesuai profil pengguna.
    * Kami memilih Gemini 2.0 secara spesifik karena kombinasi performanya yang sangat cepat (*ultra-low latency*) yang krusial untuk web interaktif, kuota gratis (*free tier*) yang sangat memadai bagi developer melalui Google AI Studio, serta dukungan *Structured Outputs* bawaan yang sangat kuat (dikombinasikan dengan Pydantic) untuk menjamin data JSON yang dihasilkan LLM selalu valid tanpa halusinasi format—sesuatu yang sering memerlukan trik *prompt engineering* rumit pada model lain.
*   **Data Validation:** [Pydantic](https://docs.pydantic.dev/) digunakan untuk memastikan *output* dari Gemini AI selalu berupa skema JSON yang valid dan konsisten.
*   **Data Visualization:** [Plotly Graph Objects](https://plotly.com/python/) digunakan untuk menyajikan bagan analisis investasi dan penghematan emisi secara interaktif.
*   **Live Data Fetcher (Scraper/API):** Menggunakan `requests` dan `beautifulsoup4` untuk menarik data harga BBM dan listrik PLN terkini secara dinamis saat aplikasi dijalankan.

---

## 2. Cara Mengakses & Menjalankan Aplikasi

Aplikasi GreenSwitch telah di-*deploy* secara langsung (live) ke cloud, sehingga Anda tidak perlu melakukan instalasi atau pengaturan *environment* lokal apa pun. 

Cukup buka tautan berikut melalui browser komputer Anda:
 **[https://greenswitch-rdr.streamlit.app/](https://greenswitch-rdr.streamlit.app/)**

### Skenario Penggunaan Aplikasi:
1. **Memulai Analisis:** Di halaman depan (Hero Section), baca sekilas lalu klik tombol hijau **"Mulai Analisis ➔"**.
2. **Mengisi Profil Kendaraan:** Anda akan masuk ke bagian formulir. Silakan pilih jenis kendaraan BBM Anda saat ini (misal: Motor Matic), lalu masukkan estimasi jarak tempuh harian Anda menggunakan *slider*. Tentukan juga budget Anda jika ingin membeli EV (misal: Rp 20 Juta).
3. **Kalkulasi Cerdas AI:** Klik tombol **"✨ Analisis dengan Agent"**. Sistem akan otomatis menarik harga BBM Pertalite/Pertamax secara langsung dari internet, mencocokkannya dengan profil Anda, dan meracik rekomendasi finansial.
4. **Membaca Laporan ROI:** Sebuah laporan rapi akan muncul. Anda bisa melihat perbandingan pengeluaran BBM vs Listrik per bulan, jumlah bulan hingga balik modal (*Break Even Point*), dan daftar unit mobil/motor EV asli (lengkap dengan harga dan daya jelajahnya) yang direkomendasikan AI khusus untuk Anda.
5. **Diskusi Lanjutan (Chatbot AI):** Jika Anda masih ragu atau punya pertanyaan lain, *scroll* ke bagian paling bawah. Terdapat kolom chat di mana Anda bisa mengobrol santai dengan AI (Contoh: *"Dari rekomendasi motor EV tadi, mana yang paling tahan banjir?"*). AI akan menjawab berdasarkan konteks profil Anda.

## 3. Cara Mengganti API Key (Jika Terkena Limit / Kuota Habis)

Aplikasi ini menggunakan API Key Google Gemini agar fitur kecerdasan buatan dapat bekerja. Jika Anda menemui error seperti `Resource Exhausted`, `Quota Exceeded`, atau fitur chat mati total, artinya API Key sedang limit dan Anda harus menggantinya.

**API KEY alternatif yang dapat digunakan**
1. AIzaSyDtjBLKueN0l8wOsqJSVWjMvp5DRP5NZWM
2. AIzaSyD19lP8AxRZuj8fvKlIf3NBx6VSXQmNHYk

**Langkah Mengganti API Key:**
1. Kunjungi situs [Google AI Studio](https://aistudio.google.com/app/apikey) dan login menggunakan akun Google Anda.
2. Klik tombol **"Create API key"** di project baru Anda untuk membuat kunci rahasia secara gratis. Salin (Copy) kode yang diberikan (diawali dengan `AIzaSy...`).
3. Buka berkas **`app.py`** menggunakan Text Editor (VS Code, Notepad, dll).
4. Cari baris **ke-46** yang berisi penugasan `DEFAULT_API_KEY`:
   ```python
   # --- Setup API Key ---
   DEFAULT_API_KEY = "AIzaSyC0Uu6OnFL7SEELAMn0f-R745GqfMYMdbc"
   ```
5. Ganti teks string tersebut dengan API key baru yang Anda salin dari AI Studio:
   ```python
   DEFAULT_API_KEY = "MASUKAN_API_KEY_ANDA_YANG_BARU_DI_SINI"
   ```
6. **Simpan file (`Ctrl+S`)**.
7. Jika di lokal, aplikasi akan me- *reload* secara otomatis. Jika di Cloud (seperti GitHub ke Streamlit Cloud), lakukan *commit* dan *push* perubahan tersebut ke GitHub untuk menerapkan API Key baru di server online.


---

## 4. Penjelasan Mekanisme Scraping & API Fetching

GreenSwitch tidak menggunakan basis data statis untuk menghitung biaya BBM dan listrik. Aplikasi ini memuat modul `scraper.py` untuk menarik dua data utama secara *real-time* sebelum AI melakukan kalkulasi:

1. **Harga BBM Terkini:** Mengambil struktur harga JSON publik secara langsung dari REST API resmi MyPertamina (`https://api.web.mypertamina.id/price`). Data yang difilter adalah Pertalite, Pertamax, dan Pertamax Turbo di wilayah DKI Jakarta.
2. **Tarif Listrik PLN:** Menggunakan BeautifulSoup untuk me-*scrape* tabel penyesuaian tarif (*Tariff Adjustment*) dari halaman publik Wikipedia yang berisi data tarif per kWh.

### Mengapa Hanya Data Ini yang Diambil Secara Live?
Dua variabel ini (Harga BBM non-subsidi dan Tarif Penyesuaian Listrik) **bersifat sangat fluktuatif** dan kebijakan penyesuaian harga (naik/turun) sering kali diterapkan oleh pemerintah setiap bulannya. 

Mengambil data ini secara *real-time* adalah langkah **sangat krusial** agar perhitungan komparasi biaya operasional dan ROI (Return of Investment) dari *AI Agent* selalu menggunakan angka pasar hari ini, sehingga laporan kelayakan yang diberikan terhindar dari bias data statis yang sudah usang.

Sedangkan untuk variabel lain (misal: harga mobil EV di pasaran), kita mengandalkan keluasan wawasan dari Large Language Model (Gemini) itu sendiri yang sudah memiliki basis pengetahuan harga pasar mobil tanpa perlu dilakukan *scraping* berlebihan yang membebani server aplikasi.
