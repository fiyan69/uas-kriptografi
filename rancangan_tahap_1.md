# Tahap 1 — Rancangan Benchmark dan Pelabelan

Proyek: Evaluasi Klasifikasi Machine Learning untuk Pemilihan Enkripsi Dinamis Berbasis Ukuran File dan Beban Komputasi  
Kelompok: Andi Rafiyan (237006074), Arya Achmad Caesar (237006093)

## Status
Rancangan awal disetujui pengguna. Simpan keputusan ini sebagai acuan konsisten untuk implementasi Tahap 2. Detail teknis yang belum ditentukan ditandai terbuka; jangan menganggapnya sudah disetujui.

## Benchmark

- Algoritma: AES-128-CTR, AES-256-CTR, ChaCha20, dan 3DES-CTR.
- Pengukuran utama: enkripsi saja (*encrypt-only*), tanpa protokol autentikasi. Tujuannya membandingkan biaya enkripsi; hasilnya bukan rekomendasi protokol komunikasi lengkap yang aman.
- 3DES hanya pembanding algoritma legacy, bukan rekomendasi penggunaan keamanan modern.
- Ukuran payload: 1 KB, 10 KB, 100 KB, 1 MB, 10 MB, 50 MB.
- Benchmark ukur kondisi sistem apa adanya; tidak ada kelas `idle`/`loaded` atau beban latar buatan. Setiap putaran mengacak urutan empat algoritma. Catat CPU aktual sebelum tiap enkripsi sebagai fitur numerik.
- Ulangan: 5 warm-up algoritma (tidak dicatat), lalu 30 putaran tercatat per ukuran file; tiap putaran mengukur tiap algoritma sekali.

## Metrik dan prosedur ukur yang disepakati

- Pustaka implementasi: `pycryptodome` (perlu mencatat versi aktual saat eksperimen).
- Gunakan AES-128-CTR, AES-256-CTR, ChaCha20, dan 3DES-CTR. Buat objek cipher baru pada tiap pengukuran; gunakan nonce/counter baru dan payload yang sama untuk semua algoritma pada kombinasi ukuran/kondisi tersebut.
- Ukur enkripsi dengan `time.perf_counter_ns()`. Untuk payload kecil, ulangi enkripsi memakai objek cipher yang sama hingga jendela ukur minimal 1 detik; catat waktu rata-rata per enkripsi. Pembuatan payload dan inisialisasi cipher tidak masuk waktu.
- CPU: gunakan `time.thread_time_ns()` pada thread enkripsi, bukan `psutil` atau waktu seluruh proses, agar thread sampler tidak ikut terhitung. Persentase = waktu CPU thread ÷ waktu nyata × 100; catat bahwa hasil menunjukkan penggunaan thread enkripsi.
- Memori: gunakan `psutil` untuk mengambil RSS awal dan RSS puncak selama enkripsi dengan sampling tiap 10 ms; catat puncak dikurangi RSS awal. Sampling dapat melewatkan lonjakan yang lebih singkat dari interval tersebut.
- Ukur CPU sistem aktual (`system_cpu_usage_percent`) sebelum tiap enkripsi; nilainya menjelaskan kondisi perangkat saat itu, bukan beban yang dikendalikan.
- Simpan 30 pengukuran mentah per algoritma dan ukuran file. Keputusan terbaru memakai pengelompokan empat algoritma per putaran, bukan rentang CPU. CPU aktual dicatat sebagai konteks; label tidak membuktikan pemenang pada CPU yang identik. Arahan awal tentang pengelompokan rentang CPU digantikan keputusan label per putaran di bawah.
- Catat `file_size_bytes`, `algorithm`, `system_cpu_usage_percent`, `initial_ram_usage_percent`, `execution_time_seconds`, `process_cpu_usage_percent`, `memory_peak_delta_bytes`, `throughput_mb_per_sec`, nomor ulangan, serta metadata lingkungan.
- Fitur prediksi: ukuran file, CPU aktual sebelum enkripsi, dan RAM awal. Metrik hasil enkripsi tidak menjadi fitur prediksi.

Simpan hasil mentah tanpa manipulasi ke `raw_dataset.csv`. Versi pustaka dan lingkungan dicatat agar eksperimen dapat direproduksi.

## Formula label yang disepakati

- Setiap putaran (`round_id`) memuat satu pengukuran dari tiap algoritma pada ukuran file yang sama. Label putaran dihitung dari empat pengukuran tersebut, dengan CPU aktual dicatat sebagai konteks eksperimen.
- Normalisasikan waktu, CPU thread, dan delta memori di antara empat hasil dalam putaran yang sama.
- Skor gabungan: waktu 70%, CPU 20%, memori 10%; skor terendah menjadi `optimal_algorithm`. Jika seri, throughput tertinggi menang.
- Setiap baris putaran menyimpan label putaran yang sama; 30 putaran memberi pengukuran berulang untuk ukuran tersebut.
- Label menunjukkan terbaik menurut skor performa/resource pada putaran itu, bukan paling aman atau rekomendasi produksi. 3DES tetap pembanding legacy.

## Hal yang masih perlu dikunci sebelum analisis lanjutan

1. Penanganan kegagalan pengukuran dan skor seri setelah melihat sebaran data.
2. Protokol autentikasi tidak termasuk benchmark utama; bila diperlukan, bahas terpisah sebagai ekstensi AEAD yang sebanding.

## Catatan batas interpretasi

Eksperimen mengukur performa encrypt-only. Tanpa autentikasi, benchmark ini tidak mengevaluasi integritas/autentisitas data dan tidak boleh disajikan sebagai rancangan sistem enkripsi lengkap untuk deployment. Label berbobot menyatakan preferensi performa-resource berdasarkan bobot yang disepakati, bukan ukuran keamanan kriptografi.

## Tahap berikutnya

Sebelum membuat skrip Tahap 2, sepakati definisi ukur CPU/memori, rincian implementasi cipher, dan agregasi label. Setelah keputusan tersebut jelas, implementasikan benchmark untuk menghasilkan `raw_dataset.csv`.
