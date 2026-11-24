# Project Overview: Machine Learning-Based Cryptographic Algorithm Selection

## 1. Informasi Umum Proyek

* **Mata Kuliah:** Kriptografi (Tugas Project-Based Learning / UAS)

* **Topik Utama:** Machine Learning-Based Cryptographic Algorithm Selection

* **Judul Penelitian:** Evaluasi Klasifikasi Machine Learning untuk Pemilihan Enkripsi Dinamis Berbasis Ukuran File dan Beban Komputasi

* **Pelaksana (Kelompok):**

  1. Andi Rafiyan (237006074)

  2. Arya Achmad Caesar (237006093)

## 2. Latar Belakang & Tujuan Penelitian

### Latar Belakang

Dalam sistem keamanan informasi, proses enkripsi sering kali menggunakan satu algoritma statis (misalnya AES-256) untuk semua jenis dan ukuran data. Padahal, ukuran file yang bervariasi serta kondisi beban komputasi perangkat (CPU dan RAM) yang dinamis sangat memengaruhi efisiensi waktu eksekusi dan konsumsi sumber daya. Penggunaan algoritma yang terlalu berat untuk data kecil atau saat beban sistem tinggi dapat menurunkan performa aplikasi.

### Tujuan Penelitian

Membangun dan mengevaluasi model klasifikasi *Machine Learning* yang mampu memilih algoritma enkripsi paling optimal secara adaptif berdasarkan karakteristik ukuran file dan beban komputasi perangkat saat proses berlangsung.

## 3. Target Output (Deliverables)

Sesuai dengan instruksi tugas perkuliahan, proyek ini harus menghasilkan 5 output utama:

1. **Laporan Project-Based:** Dokumen ilmiah lengkap (Pendahuluan, Tinjauan Pustaka, Metodologi, Hasil & Pembahasan, Kesimpulan).

2. **20 Referensi Penunjang:** Minimal 20 jurnal/paper relevan terkait *adaptive cryptography*, *encryption benchmarking*, dan *ML classification*, yang dikumpulkan dalam dua fase (5–8 referensi inti di awal, lalu melengkapi sisa 12–15 referensi secara paralel saat tahap eksperimen dan penulisan laporan).

3. **Hasil Eksperimen:** Metrik evaluasi model ML (Accuracy, Precision, Recall, F1-Score, Confusion Matrix) serta grafik perbandingan performa antar algoritma kriptografi.

4. **Dataset:** File CSV hasil pengujian *benchmark* mandiri (`raw_dataset.csv` dan `labeled_dataset.csv`).

5. **PPT (Slide Presentasi):** Materi presentasi ringkas dan visual untuk pemaparan hasil proyek.

## 4. Strategi Dataset & Kredibilitas Ilmiah

### Mengapa Membuat Dataset Sendiri?

Dataset publik yang siap pakai (*plug-and-play*) untuk skenario pemilihan algoritma kriptografi berdasarkan metrik *hardware* (CPU, RAM, ukuran file) sangat langka di platform seperti Kaggle atau Hugging Face. Selain itu, metrik performa enkripsi sangat bergantung pada spesifikasi perangkat keras (*hardware-dependent*). Oleh karena itu, pembuatan dataset melalui *empirical benchmarking* mandiri di lingkungan sistem yang terkontrol adalah pendekatan standar yang valid.

### Standar Transparansi & Anti-Manipulasi

Untuk menjaga kredibilitas ilmiah dan memastikan eksperimen dapat direproduksi (*reproducible*), penelitian ini menerapkan prinsip berikut:

* **Dokumentasi Lingkungan:** Mencatat spesifikasi hardware (CPU, RAM, Storage), OS, versi Python, dan versi library secara eksplisit.

* **Kontrol Keacakan:** Menggunakan *random seed* (`random_state`) yang tetap saat membangkitkan data uji sintetis maupun saat membagi data latih/uji.

* **Pemisahan Data:** Menyimpan `raw_dataset.csv` (hasil pengukuran mentah tanpa modifikasi) secara terpisah dari `labeled_dataset.csv`.

* **Aturan Pelabelan Objektif:** Penentuan label algoritma terbaik (`optimal_algorithm`) didasarkan pada formula matematis/logika terukur (menyeimbangkan waktu eksekusi dan beban resource), bukan penilaian subjektif.

* **Perbandingan Baseline:** Membandingkan performa model ML dengan aturan statis sederhana (*if-else baseline*).

## 5. Spesifikasi Teknis & Desain Eksperimen

* **Bahasa Pemrograman:** Python (3.8+)

* **Library Utama:**

  * `cryptography` / `pycryptodome` (Implementasi algoritma enkripsi)

  * `psutil` (Pemantauan beban CPU dan penggunaan RAM secara real-time)

  * `pandas` & `numpy` (Pengolahan data dan manipulasi CSV)

  * `scikit-learn` (Pelatihan dan evaluasi model Machine Learning)

  * `matplotlib` / `seaborn` (Visualisasi grafik eksperimen)

* **Algoritma Kriptografi yang Diuji:** `AES-128`, `AES-256`, `ChaCha20`, dan `TripleDES` (3DES).

* **Algoritma Machine Learning (Klasifikasi):** *Decision Tree*, *Random Forest*, dan perbandingan dengan *K-Nearest Neighbors (KNN)* atau *Logistic Regression*.

* **Skema Fitur Dataset (Features):**

  * `file_size_bytes` / `file_size_kb`: Ukuran payload yang dienkripsi (rentang 1 KB hingga 50 MB).

  * `initial_cpu_usage`: Persentase beban CPU sebelum proses enkripsi dimulai.

  * `initial_ram_usage`: Persentase penggunaan RAM sebelum proses enkripsi dimulai.

  * `execution_time`: Waktu yang dibutuhkan untuk menyelesaikan enkripsi (detik).

  * `process_cpu_usage_percent`: Persentase waktu CPU thread enkripsi terhadap waktu nyata dalam interval yang sebanding, sebelum penghentian sampler. Menggantikan usulan awal `cpu_delta` / `peak_cpu`; bukan lonjakan CPU sistem atau seluruh proses.

  * `memory_used`: Konsumsi memori selama proses berlangsung.

  * `throughput`: Kecepatan pemrosesan data (MB/s).

  * `optimal_algorithm` (**Target Label**): Kelas algoritma terbaik untuk kondisi baris tersebut.

## 6. Pemetaan Workflow Penelitian

### Tahap 0: *Initial Literature Scoping* (5–8 Referensi Inti)

* Menjaring 5–8 jurnal/paper kunci terkait *adaptive cryptography*, *encryption performance benchmarking*, dan klasifikasi *machine learning*.

* Mengunci dasar pemilihan algoritma kriptografi, metrik evaluasi sistem, serta keseragaman terminologi sebagai pedoman teknis sebelum masuk ke tahap pengujian.

### Tahap 1: Perencanaan & Persiapan Lingkungan Uji

* Menetapkan ruang lingkup algoritma kriptografi yang dibandingkan (`AES-128`, `AES-256`, `ChaCha20`, `3DES`).

* Menentukan variasi ukuran file uji (1 KB, 10 KB, 100 KB, 1 MB, 10 MB, 50 MB). Skenario normal vs. beban latar merupakan rencana awal; berdasarkan keputusan pengguna, implementasi mengukur CPU aktual tanpa beban buatan dan tanpa klaim idle/loaded terkontrol. Urutan empat algoritma diacak per putaran.

* Mencatat spesifikasi hardware, OS, versi Python, dan library yang digunakan.

* Menyiapkan *random seed* terkontrol untuk pembangkitan data uji sintetis.

### Tahap 2: Pembuatan Dataset Mentah (*Data Generation & Benchmarking*)

* Membuat script Python untuk membangkitkan file uji (*dummy/synthetic payloads*) dengan berbagai ukuran terukur.

* Menjalankan *looping* proses enkripsi untuk setiap kombinasi ukuran file dan algoritma kriptografi.

* Mengukur dan mencatat metrik kinerja (`file_size`, `algorithm`, `execution_time`, `cpu_usage`, `memory_usage`, `throughput`).

* Menyimpan seluruh hasil pengukuran mentah tanpa perubahan manual. Raw aktif setelah benchmark ulang disetujui adalah `raw_dataset_cpu_corrected.csv`; `raw_dataset.csv` historis tetap utuh sebagai arsip. Lihat `HASIL_AKTIF.md` dan `status_audit_tahap_1_4.md` untuk pemetaan artefak penelitian.

### Tahap 3: *Preprocessing* & Pelabelan Terukur (*Labeling*)

* Melakukan pembersihan data (*data cleaning*), mengecek *missing values*, dan menangani anomali/spike ekstrem akibat proses latar belakang OS.

* Merumuskan dan menerapkan fungsi/aturan pelabelan matematis yang objektif untuk menentukan kolom `optimal_algorithm` pada setiap skenario pengujian.

* Menyimpan hasil akhir ke dalam `labeled_dataset.csv` sebagai dataset utama penelitian.

### Tahap 4: Pelatihan & Evaluasi Model *Machine Learning*

* Membagi putaran utuh menjadi data latih dan data uji 80:20 dengan seed 42; menerapkan 5-Fold Cross Validation hanya pada bagian 80% data latih. Holdout 20% tidak dipakai untuk memilih model/parameter. Karena data eksperimen lama telah dievaluasi sebelumnya, jangan menyebut holdout historis sebagai data yang belum pernah diperiksa.

* Memasang pagar IQR hanya dari train setiap split/fold dan menerapkannya ke test sebelum pelabelan lokal putaran. Metrik strata ukuran file yang tidak tersedia di train dibiarkan mentah, diberi penanda tidak dikoreksi; jangan gunakan pagar lintas ukuran. Jika waktu dikoreksi, throughput dihitung ulang. Dataset berlabel penuh bersifat deskriptif, bukan sumber label global untuk evaluasi.

* Melatih beberapa model klasifikasi tabular (seperti *Decision Tree* dan *Random Forest*).

* Mengevaluasi kinerja model menggunakan metrik *Accuracy*, *Precision*, *Recall*, *F1-Score*, dan *Confusion Matrix*, lalu membandingkannya dengan *baseline* statis.

### Tahap 5: Analisis Hasil, Kelengkapan 20 Referensi, Laporan & PPT

* Membuat visualisasi grafik perbandingan kecepatan eksekusi, konsumsi *resource* antar algoritma, serta grafik performa model ML.

* Melengkapi sisa 12–15 referensi jurnal/paper pendukung (yang dikumpulkan secara paralel selama proses eksperimen dan penulisan) hingga genap 20 referensi relevan.

* Menyusun Laporan Project-Based secara sistematis beserta slide presentasi (PPT) sebagai deliverables akhir.