# Grafik Hasil Eksperimen

## Sumber

Raw aktif `raw_dataset_cpu_corrected.csv` (720 pengukuran, 180 putaran), label deskriptif `labeled_dataset.csv`, dan `output_cpu_corrected/evaluation_final.json`. Grafik tidak melatih ulang model atau mengubah data. Hash sumber dan daftar gambar tercatat di `manifest_grafik.json`.

## Daftar dan penggunaan

1. `01_execution_time_seconds`: waktu per enkripsi dalam ms, skala log.
2. `02_throughput_mb_per_sec`: throughput dalam MiB/s, skala log. Nama kolom historis menyebut MB, tetapi rumus memakai 1024² byte.
3. `03_process_cpu_usage_percent`: penggunaan CPU thread enkripsi, bukan CPU total perangkat.
4. `04_memory_peak_delta_bytes`: selisih peak RSS terhadap baseline, disajikan MiB; bukan RAM total perangkat atau alokasi cipher murni.
5. `05_distribusi_label`: satu label per putaran pada dataset deskriptif penuh setelah winsorization. Jangan menghitung empat baris algoritma sebagai empat sampel independen.
6. `06_model_cv`: akurasi dan macro-F1 pooled dari lima fold hanya pada 144 putaran train.
7. `07_model_holdout`: akurasi dan macro-F1 pada 36 putaran terpisah dari CV.
8. `08_model_ukuran_baru`: metrik pooled leave-one-file-size-out, 180 prediksi.
9–11. `09_confusion_matrix_cv`, `10_confusion_matrix_holdout`, `11_confusion_matrix_ukuran_baru`: setiap gambar berisi empat model; baris aktual, kolom prediksi, angka jumlah putaran. Warna sebanding antarmodel di gambar yang sama; baca angka sel, bukan membandingkan warna antar-gambar.
12. `12_variasi_akurasi_cv`: akurasi setiap fold, ukuran test 29/29/29/29/28 putaran.

Setiap grafik tersedia sebagai PNG 300 dpi untuk laporan/PPT dan SVG untuk penyuntingan vektor. `ringkasan_benchmark.csv` menyediakan angka median/Q1/Q3 per algoritma/ukuran; `ringkasan_metrik_model.csv` menyediakan semua empat metrik model (skala 0–1).

## Cara membaca grafik benchmark

Garis menampilkan median 30 pengukuran mentah per algoritma dan ukuran; area berwarna adalah Q1–Q3, bukan confidence interval. Kuartil grafik memakai NumPy percentile interpolasi linear untuk ringkasan deskriptif; berbeda dari kuartil median-halves pagar IQR pada preprocessing, tidak mengubah aturan label/evaluasi. Sumbu ukuran adalah kategori berurutan berjarak sama, bukan jarak proporsional byte. KiB=1024 byte; MiB=1048576 byte.

Waktu dan throughput logaritmik agar 3DES dan AES tetap terbaca bersama. Memori/CPU menggunakan sumbu linear mulai nol. Delta RSS nol mungkin berasal dari sampling/allocator dan bukan bukti algoritma tidak memakai memori.

## Batas kesimpulan

Jangan mencampur CV, holdout, dan uji ukuran baru. Macro-F1 pada grafik adalah perhitungan atas prediksi gabungan, bukan rata-rata F1 fold. Mean/std fold tersedia dalam JSON evaluasi. Penelitian satu perangkat, encrypt-only, CPU aktual tanpa skenario loaded terkontrol. Performa klasifikasi belum konsisten; grafik tidak membuktikan keunggulan signifikan atau sistem produksi andal. 3DES diuji tetapi tidak muncul sebagai label pemenang.

## Reproduksi

Dari folder proyek: `py buat_grafik_eksperimen.py` (memerlukan NumPy dan matplotlib; runtime pembuatan matplotlib 3.11.2). Skrip memakai assert untuk jumlah sampel, konsistensi label, jumlah confusion matrix, nilai hingga, dan hash sumber sebelum/sesudah. Ringkasan numerik serta metrik berasal langsung dari sumber aktif.

PNG waktu dan confusion matrix diperiksa visual: judul, angka, sumbu, dan catatan terbaca; grafik penuh tidak terpotong. Seluruh PNG diverifikasi dapat dibuka dan SVG valid XML.

Untuk serah-terima, paket grafik merupakan tambahan ZIP proyek sebelumnya; laporan lengkap, penambahan referensi hingga 20, serta PPT tetap pekerjaan selanjutnya.
