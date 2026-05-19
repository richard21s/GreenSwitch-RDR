import os
import json
import logging
import google.generativeai as genai
from scraper import get_bbm_price, get_pln_tariffs, get_ev_database

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)

class EnergyTransitAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
            try:
                # Cari model yang tersedia dan mendukung generateContent
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                if available_models:
                    # Pilih model gemini-1.5-flash jika ada, kalau tidak pakai yang pertama tersedia
                    target_model = next((m for m in available_models if '1.5-flash' in m), available_models[0])
                    self.model = genai.GenerativeModel(target_model)
                    self.chat_session = self.model.start_chat(history=[])
                else:
                    self.model = None
                    logging.error("Tidak ada model Gemini yang mendukung generateContent.")
            except Exception as e:
                self.model = None
                logging.error(f"Gagal menginisialisasi model: {e}")
        else:
            self.model = None
            self.chat_session = None

    def calculate_metrics(self, kendaraan_jenis, konsumsi_km_per_liter, jenis_bbm, jarak_km, pln_tarif, anggaran_juta, trade_in_juta=0):
        bbm_price = get_bbm_price(jenis_bbm)
        
        # Biaya BBM Bulanan
        biaya_bbm_bulanan = ((jarak_km * 30) / konsumsi_km_per_liter) * bbm_price
        
        # Kwh Per Bulan (Asumsi Motor EV 25 km/kWh, Mobil EV 7 km/kWh)
        kwh_per_km = (1 / 25) if kendaraan_jenis == "motor" else 0.14
        kwh_per_bulan = (jarak_km * 30) * kwh_per_km
        biaya_listrik_bulanan = kwh_per_bulan * pln_tarif
        
        # Selisih & Emisi
        selisih_bulanan = biaya_bbm_bulanan - biaya_listrik_bulanan
        emisi_co2_bulan = (jarak_km * 30 * 0.075) if kendaraan_jenis == "motor" else (jarak_km * 30 * 0.23)
        net_cost_juta = max(0, anggaran_juta - trade_in_juta)
        break_even_bulan = round((net_cost_juta * 1000000) / selisih_bulanan) if selisih_bulanan > 0 else None
        
        return {
            "biaya_bbm_bulanan": biaya_bbm_bulanan,
            "biaya_listrik_bulanan": biaya_listrik_bulanan,
            "selisih_bulanan": selisih_bulanan,
            "emisi_co2_bulan": emisi_co2_bulan,
            "break_even_bulan": break_even_bulan,
            "bbm_price_used": bbm_price
        }

    def find_ev_matches(self, kategori_ev_diinginkan, anggaran_juta):
        ev_db = get_ev_database()
        
        # Mapping kategori UI ke tipe database internal
        if kategori_ev_diinginkan == "Motor":
            target_tipe = "motor"
        elif kategori_ev_diinginkan == "Mobil City Car":
            target_tipe = "mobil_kecil"
        else: # Sedan/MPV dan SUV
            target_tipe = "mobil_besar"
            
        matches = [ev for ev in ev_db if ev["harga"] <= anggaran_juta and ev["tipe"] == target_tipe]
        # Sort by price descending and return top 3
        matches.sort(key=lambda x: x["harga"], reverse=True)
        return matches[:3]

    def analyze(self, user_profile):
        """
        user_profile dict:
        {
            "kendaraan_jenis": str,
            "konsumsi_km_per_liter": float,
            "jarak_km": int,
            "pln_label": str,
            "pln_tarif": int,
            "anggaran_juta": float
        }
        """
        metrics = self.calculate_metrics(
            user_profile["kendaraan_jenis"],
            user_profile["konsumsi_km_per_liter"],
            user_profile["jenis_bbm"],
            user_profile["jarak_km"],
            user_profile["pln_tarif"],
            user_profile["anggaran_juta"],
            user_profile.get("trade_in_juta", 0)
        )
        
        ev_matches = self.find_ev_matches(user_profile.get("kategori_ev_diinginkan", "Mobil City Car"), user_profile["anggaran_juta"])

        if not self.model:
            # Fallback statis jika API Key belum dimasukkan
            return self._fallback_analysis(metrics, ev_matches, user_profile)

        # Gunakan Gemini API untuk reasoning
        prompt = f"""
        Kamu adalah "GreenSwitch AI Agent", seorang penasihat transisi energi dan ekonomi.
        Tugasmu: Menganalisis kelayakan pengguna untuk beralih ke Kendaraan Listrik (EV) berdasarkan prinsip Keadilan Sosial (Social Equity) dan Lingkungan.

        Data Pengguna:
        - Kendaraan BBM saat ini: {user_profile['kendaraan_jenis']} ({user_profile['konsumsi_km_per_liter']} km/liter) menggunakan BBM jenis {user_profile['jenis_bbm']}
        - Jarak Tempuh Harian: {user_profile['jarak_km']} km
        - Target Kategori EV yang Ingin Dibeli: {user_profile.get('kategori_ev_diinginkan', 'Mobil')}
        - Anggaran Beli EV: Rp {user_profile['anggaran_juta']} Juta
        - Nilai Jual Kendaraan Lama (Trade-in): Rp {user_profile.get('trade_in_juta', 0)} Juta
        - Biaya Investasi Bersih (Anggaran - Trade-in): Rp {max(0, user_profile['anggaran_juta'] - user_profile.get('trade_in_juta', 0))} Juta
        - Tarif PLN di rumah: {user_profile['pln_label']} (Rp {user_profile['pln_tarif']}/kWh)
        
        Hasil Kalkulasi Tool:
        - Harga BBM: Rp {metrics['bbm_price_used']}/liter
        - Biaya BBM bulanan saat ini: Rp {int(metrics['biaya_bbm_bulanan'])}
        - Biaya listrik EV bulanan (estimasi): Rp {int(metrics['biaya_listrik_bulanan'])}
        - Selisih penghematan per bulan: Rp {int(metrics['selisih_bulanan'])}
        - Emisi CO2 yang dihemat per bulan: {metrics['emisi_co2_bulan']:.1f} kg
        - Kendaraan EV yang pas dengan anggaran: {[ev['nama'] for ev in ev_matches] if ev_matches else "Tidak ada yang cocok di bawah anggaran"}
        
        ATURAN KEPUTUSAN & INVESTASI:
        1. Jika penghematan finansial kecil (< Rp 100.000/bulan) DAN anggaran sangat besar tapi tidak logis untuk transisi, sarankan "Tunda Dulu" (Wait). Ini mencegah pengguna dari kelas ekonomi manapun menghamburkan uang tanpa benefit nyata.
        2. Jika tidak ada EV yang cocok dengan budget, sarankan "Tunda Dulu" dan tabung uangnya (Wait).
        3. Jika penghematan signifikan dan ada budget yang pas, dorong untuk beralih "Transisi Sekarang" (Switch).
        4. Transparan, objektif, tanpa bias.
        5. REKOMENDASI INVESTASI: Jika keputusan adalah "Tunda Dulu" (wait) atau "Netral" (neutral) dan pengguna memiliki dana/anggaran sisa yang signifikan, berikan saran secara spesifik dan eksplisit untuk mengalokasikan atau menginvestasikan dana tersebut ke instrumen finansial lain (seperti emas, reksa dana, obligasi, atau saham) daripada membiarkannya menganggur atau memaksakan beli EV yang belum efisien. Masukkan poin ini ke dalam penjelasan narasi dan analisis mendalam.

        Output WAJIB berupa JSON yang valid dengan skema berikut, TANPA markdown block (hanya raw JSON):
        {{
            "verdict": "switch" | "wait" | "neutral",
            "title": "Judul Singkat Keputusan (max 5 kata)",
            "narasi": "Penjelasan paragraf yang empatik, logis, menjelaskan hitungan finansial & lingkungan, serta saran alternatif investasi/alokasi dana jika keputusan tunda, sekitar 45-55 kata.",
            "analisis_mendalam": "Teks berformat Markdown yang berisi analisis komprehensif. WAJIB terdiri dari 5 bagian dengan subjudul berikut (gunakan ### untuk subjudul): \\n### Analisis Biaya\\n...\\n### Dampak Lingkungan\\n...\\n### Rekomendasi Kendaraan\\n...\\n### Titik Balik Modal (BEP)\\n...\\n### Kesimpulan & Alternatif Investasi\\n...",
            "tips": [
                {{"highlight": "KataAwal", "text": "lanjutan tips 1"}},
                {{"highlight": "KataAwal", "text": "lanjutan tips 2"}},
                {{"highlight": "KataAwal", "text": "lanjutan tips 3"}}
            ]
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            # Membersihkan respons barangkali ada blok ```json
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            
            # Memperbarui chat session history agar bisa lanjut tanya jawab
            self.chat_session = self.model.start_chat(history=[
                {"role": "user", "parts": [prompt]},
                {"role": "model", "parts": [text_response]}
            ])
            
            result_json = json.loads(text_response)
            result_json["metrics"] = metrics
            result_json["evMatches"] = ev_matches
            return result_json

        except Exception as e:
            logging.error(f"Error calling Gemini API: {e}")
            return self._fallback_analysis(metrics, ev_matches, user_profile)

    def chat(self, user_message):
        """
        Handle follow-up chat with context.
        """
        if not self.chat_session:
            return "Mohon masukkan API Key Gemini di sidebar terlebih dahulu."
        
        try:
            # Instruksikan model untuk berhenti menggunakan JSON pada sesi tanya jawab
            modified_message = f"Instruksi sistem: Jawab pertanyaan berikut menggunakan bahasa manusia yang natural, ramah, dan format Markdown (JANGAN gunakan format JSON lagi).\n\nPertanyaan User: {user_message}"
            response = self.chat_session.send_message(modified_message)
            return response.text
        except Exception as e:
            logging.error(f"Error in chat: {e}")
            return "Maaf, Agent sedang mengalami gangguan saat merespons."

    def _fallback_analysis(self, metrics, ev_matches, user_profile):
        """ Hardcoded logic sama dengan prototipe React jika API gagal/tidak diset """
        is_motor = (user_profile["kendaraan_jenis"] == "motor")
        selisih = metrics["selisih_bulanan"]
        
        if is_motor and user_profile["anggaran_juta"] > 100:
            verdict = "wait"
            title = "Tunda Dulu, Alokasikan Dana untuk Investasi"
            narasi = f"Beralih ke motor listrik saat ini hanya menghemat Rp {int(selisih)}/bln. Anggaran Anda (Rp {user_profile['anggaran_juta']} jt) terlampau besar untuk pasar motor listrik. Sangat disarankan menginvestasikan dana ini ke emas atau reksa dana terlebih dahulu. (Fallback)"
        elif selisih > 300000 and len(ev_matches) > 0:
            verdict = "switch"
            title = "Ya, Waktu Terbaik Beralih ke EV"
            narasi = f"Secara finansial dan lingkungan, transisi ini sangat logis. Anda menghemat operasional Rp {int(selisih)}/bln yang akan menutup nilai investasi EV dengan cepat. (Fallback)"
        elif len(ev_matches) == 0:
            verdict = "wait"
            title = "Tunda Dulu, Sesuaikan Anggaran"
            narasi = f"Dengan anggaran Rp {user_profile['anggaran_juta']} Juta, belum ada model EV baru yang sesuai. Disarankan mengalokasikan anggaran untuk investasi obligasi/tabungan berjangka. (Fallback)"
        else:
            verdict = "neutral"
            title = "Transisi Stabil, Pertimbangkan Investasi Sampingan"
            narasi = f"Penghematan bulanan (Rp {int(selisih)}) tidak terlalu drastis. Anda bisa mempertimbangkan investasi emas/reksa dana secara berkala menggunakan sisa anggaran Anda. (Fallback)"

        analisis_mendalam = f"### Analisis Biaya\nBerdasarkan data Anda, terdapat potensi penghematan sebesar **Rp {int(selisih):,}/bulan**. {'Ini merupakan jumlah yang signifikan.' if selisih > 300000 else 'Jumlah ini mungkin terasa kecil jika dibandingkan dengan modal awal beli EV baru.'}\n\n### Dampak Lingkungan\nLangkah kecil ini akan memangkas sekitar **{metrics['emisi_co2_bulan']:.1f} kg emisi CO2** setiap bulannya ke atmosfer kita.\n\n### Rekomendasi Kendaraan\n{'Kami menemukan beberapa opsi EV yang sesuai dengan budget Anda. Silakan lihat daftar EV terdekat.' if ev_matches else 'Saat ini kami belum menemukan EV baru yang pas dengan anggaran Anda, mungkin Anda bisa melihat pasar motor/mobil listrik bekas yang berkualitas.'}\n\n### Titik Balik Modal (BEP)\n{'Estimasi investasi Anda akan kembali dalam waktu kurang lebih **' + str(metrics['break_even_bulan']) + ' bulan**.' if metrics.get('break_even_bulan') else 'Saat ini kami belum bisa memproyeksikan titik balik modal (BEP) karena nilai penghematannya belum menutupi investasi bersih.'}\n\n### Kesimpulan & Alternatif Investasi\n{narasi}"

        return {
            "verdict": verdict,
            "title": title,
            "narasi": narasi,
            "analisis_mendalam": analisis_mendalam,
            "tips": [
                {"highlight": "Sesuaikan", "text": "Evaluasi kembali anggaran Anda."},
                {"highlight": "Investasi", "text": "Alokasikan sisa anggaran atau dana EV ke emas, reksa dana, atau obligasi PLN/SBN."},
                {"highlight": "Pertimbangkan", "text": "Jika sisa dana signifikan, pertimbangkan EV roda empat."}
            ],
            "metrics": metrics,
            "evMatches": ev_matches
        }
