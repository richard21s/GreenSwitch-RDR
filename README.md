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

 > [!NOTE]
> **Penting:** Kode dalam repositori ini telah dikustomisasi dan dioptimalkan secara khusus untuk berjalan di atas arsitektur *Streamlit Cloud* (termasuk injeksi Javascript lintas-iframe khusus). Aplikasi ini **tidak disarankan untuk dijalankan di lingkungan lokal (localhost)** karena akan terjadi inkonsistensi struktur DOM dan antarmuka.

### Skenario Penggunaan Aplikasi:
1. **Memulai Analisis:** Di halaman depan (Hero Section), baca sekilas lalu klik tombol hijau **"Mulai Analisis ➔"**.
2. **Mengisi Profil Kendaraan:** Anda akan masuk ke bagian formulir. Silakan pilih jenis kendaraan BBM Anda saat ini (misal: Motor Matic), lalu masukkan estimasi jarak tempuh harian Anda menggunakan *slider*. Tentukan juga budget Anda jika ingin membeli EV (misal: Rp 20 Juta). **(Opsional)** Anda juga dapat memasukkan Gemini API Key pribadi Anda pada kolom input di kanan bawah untuk menghindari limit kuota API bersama. Status di bawah kolom input akan berubah secara reaktif untuk menunjukkan API Key yang sedang aktif.
3. **Kalkulasi Cerdas AI:** Klik tombol **"✨ Analisis dengan Agent"**. Sistem akan otomatis menarik harga BBM Pertalite/Pertamax secara langsung dari internet, mencocokkannya dengan profil Anda, dan meracik rekomendasi finansial.
4. **Membaca Laporan ROI:** Sebuah laporan rapi akan muncul. Anda bisa melihat perbandingan pengeluaran BBM vs Listrik per bulan, jumlah bulan hingga balik modal (*Break Even Point*), dan daftar unit mobil/motor EV asli (lengkap dengan harga dan daya jelajahnya) yang direkomendasikan AI khusus untuk Anda.
5. **Diskusi Lanjutan (Chatbot AI):** Jika Anda masih ragu atau punya pertanyaan lain, *scroll* ke bagian paling bawah. Terdapat kolom chat di mana Anda bisa mengobrol santai dengan AI (Contoh: *"Dari rekomendasi motor EV tadi, mana yang paling tahan banjir?"*). AI akan menjawab berdasarkan konteks profil Anda.

## 3. Konfigurasi & Penggunaan Gemini API Key

Aplikasi ini menggunakan API Key Google Gemini agar fitur kecerdasan buatan dapat bekerja. Anda harus mengganti API Key dengan mengisi bagian Gemini API Key (Opsional) pada bagian profil pengguna jika menemukan **Ciri-ciri API Key Limit / Kuota Habis** berikut ini:
- Jika fitur *chatbot* menjawab dengan kalimat: *"Maaf, agent sedang mengalami gangguan saat merespons."*
- Jika pada bagian Rekomendasi/Keputusan Agen terdapat kata-kata **"(Fallback)"** (ini menandakan AI gagal merespons dan sistem terpaksa mengeluarkan teks *default*).

**Langkah Mengganti API Key:**
1. Kunjungi situs [Google AI Studio](https://aistudio.google.com/app/apikey) dan login menggunakan akun Google Anda.
2. Klik tombol **"Create API key"** di project baru Anda untuk membuat kunci rahasia secara gratis. Salin (Copy) kode yang diberikan (diawali dengan `AIzaSy...`).
3. Masuk ke halaman formulir **Profil Kendaraan** di aplikasi GreenSwitch.
4. Pada kolom **"Gemini API Key (Opsional)"**, masukkan API Key pribadi yang sudah Anda buat.
5. Perhatikan indikator di bawah kolom tersebut yang secara reaktif berubah menjadi hijau: **"🔑 Menggunakan API Key pribadi yang Anda masukkan di atas."**
6. Klik **"✨ Analisis dengan Agent"**. Agen AI akan langsung berjalan menggunakan kuota API Key pribadi Anda sendiri secara aman.

---

## 4. Penjelasan Mekanisme Scraping & API Fetching

GreenSwitch menggunakan data terpercaya untuk menghitung biaya BBM dan listrik. Aplikasi ini memuat modul `scraper.py` untuk menarik/mengambil dua data utama sebelum AI melakukan kalkulasi:

1. **Harga BBM Terkini:** Mengambil struktur harga JSON publik secara langsung dari REST API resmi MyPertamina (`https://api.web.mypertamina.id/price`). Data yang difilter adalah Pertalite, Pertamax, dan Pertamax Turbo di wilayah DKI Jakarta.
2. **Tarif Listrik PLN:** Data tarif listrik tidak diambil secara otomatis (scraping), melainkan diacu secara faktual berdasarkan rilis resmi tabel penyesuaian tarif (*Tariff Adjustment*) dari website resmi PLN (`https://www.pln.co.id/customer-en/electricity-tariffs-en/tariff-adjustment-en`). Data ini mencakup tarif per kWh untuk berbagai golongan rumah tangga umum (R-1/900 VA hingga R-2/3500+ VA).
3. **Kalkulasi Emisi CO2 yang Dihemat (Dampak Lingkungan):**
   Aplikasi ini mengkalkulasi pengurangan emisi karbon secara presisi berdasarkan standar faktor emisi rata-rata kendaraan berbahan bakar minyak (BBM) di Indonesia:
   - **Sepeda Motor BBM:** Menggunakan faktor emisi sebesar **0,075 kg CO2 per kilometer** (atau 75 gram CO2/km).
   - **Mobil BBM:** Menggunakan faktor emisi sebesar **0,23 kg CO2 per kilometer** (atau 230 gram CO2/km).
   
   **Rumus Kalkulasi Emisi Bulanan:**
   $$\text{Emisi CO2 Bulanan yang Dihemat (kg)} = \text{Jarak Tempuh Harian (km)} \times 30 \text{ hari} \times \text{Faktor Emisi}$$
   
   Data emisi ini menjadi dasar bagi *AI Agent* untuk menyusun laporan analisis dampak lingkungan, sehingga pengguna dapat memahami secara konkret seberapa besar kontribusi transisi mereka dalam mengurangi jejak karbon global.

### Mengapa Hanya Data Ini yang Diambil Secara Live?
Dua variabel ini (Harga BBM non-subsidi dan Tarif Penyesuaian Listrik) **bersifat sangat fluktuatif** dan kebijakan penyesuaian harga (naik/turun) sering kali diterapkan oleh pemerintah setiap bulannya. 

Mengambil data ini secara *real-time* adalah langkah **sangat krusial** agar perhitungan komparasi biaya operasional dan ROI (Return of Investment) dari *AI Agent* selalu menggunakan angka pasar hari ini, sehingga laporan kelayakan yang diberikan terhindar dari bias data statis yang sudah usang.

Sedangkan untuk variabel lain, khususnya **data referensi mobil/motor Listrik (EV)** yang direkomendasikan beserta kisaran harganya, data tersebut dikumpulkan secara **manual** dengan merujuk langsung pada brosur dan situs web resmi dari masing-masing agen pemegang merek (APM) kendaraan terkait. Hal ini dilakukan untuk menjamin keakuratan tipe unit dan harga on-the-road (OTR) yang paling relevan dengan kondisi pasar saat ini, tanpa perlu membebani server dengan proses *scraping* berlebihan.
