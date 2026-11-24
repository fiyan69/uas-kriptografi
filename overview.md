# Penjelasan Proyek: Machine Learning-Based Cryptographic Algorithm Selection

## Judul Proyek
**"Analisis Performa Model Klasifikasi Machine Learning untuk Pemilihan Algoritma Enkripsi Dinamis Berdasarkan Karakteristik Ukuran File dan Beban Komputasi"**

---

## 1. Sebenarnya, Apa Sih yang Kita Bikin?
Bayangin kita mau ngirim atau nyimpen file. Biasanya sistem pakai satu algoritma enkripsi aja (misal: AES-256) buat semuanya. Padahal, kalau file-nya kecil tapi enkripsinya terlalu berat, atau sebaliknya, sistem jadi kurang efisien (bisa bikin lambat atau boros baterai).

Nah, di proyek ini, kita bikin **sistem cerdas (pakai Machine Learning)** yang bisa **milih sendiri algoritma enkripsi yang paling pas secara real-time** berdasarkan kondisi file dan beban komputer saat itu.

---

## 2. Kenapa Kita Harus Bikin Dataset Sendiri?
Karena topik ini spesifik banget, **nggak ada dataset siap pakai di internet (seperti di Kaggle)** yang angkanya cocok sama spesifikasi laptop/komputer kita. 
* Makanya, kita bakal bikin dataset sendiri dengan cara **melakukan uji coba (*benchmark*) di komputer kita**. 
* Kita bakal bikin script Python untuk ngukur seberapa cepat berbagai algoritma (misal: AES-128, AES-256, ChaCha20) mengenkripsi file dengan berbagai ukuran, sekaligus ngukur penggunaan CPU dan memorinya. Hasil catatan itu yang bakal jadi file CSV (Dataset kita).

---

## 3. Hal-Hal yang Perlu Dikerjakan

### 1. Bagian Script & Data (Pembuatan Dataset)
* **Membuat *Benchmarking Script*:** Menulis kode Python menggunakan library kriptografi (seperti `cryptography` atau `pycryptodome`) dan pemantau sumber daya (`psutil`).
* **Menjalankan Eksperimen Awal:** Melakukan uji coba enkripsi file dengan berbagai variasi ukuran (dari kecil hingga besar) ke beberapa algoritma pilihan.
* **Mengumpulkan Output CSV:** Menyimpan metrik hasil pengujian (ukuran file, waktu eksekusi, penggunaan CPU, memori, dll.) ke dalam file `.csv` yang akan menjadi dataset utama proyek.

### 2. Bagian Machine Learning & Eksperimen Model
* **Preprocessing Data:** Membersihkan data CSV hasil *benchmark* dan menentukan aturan pelabelan (*labeling*) untuk menentukan algoritma mana yang paling optimal di setiap baris data.
* **Pelatihan Model (*Training*):** Memasukkan dataset ke model klasifikasi Machine Learning (menggunakan *Decision Tree* atau *Random Forest* dari *scikit-learn*).
* **Evaluasi & Metrik:** Menguji performa model menggunakan data *testing* dan mencatat tingkat akurasi, *precision*, serta *recall* untuk dijadikan grafik hasil eksperimen.

### 3. Bagian yang Dikelola/Dikerjakan Bersama
* **Penyusunan 20 Referensi:** Bersama-sama mencari, membaca, dan merangkum minimal 20 jurnal/paper pendukung dari Google Scholar atau IEEE.
* **Pembuatan Laporan Proyek:** Menulis isi laporan lengkap (Pendahuluan, Metodologi, Hasil Eksperimen, hingga Kesimpulan) berdasarkan data yang sudah didapat dari eksperimen.
* **Pembuatan Slide PPT:** Merancang materi presentasi dan grafik visual untuk persiapan sidang/pengumpulan tugas ke dosen.