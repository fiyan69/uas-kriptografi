# Tahap 0 — Matriks Telaah Awal Referensi Inti

Proyek: Evaluasi Klasifikasi Machine Learning untuk Pemilihan Enkripsi Dinamis Berbasis Ukuran File dan Beban Komputasi  
Kelompok: Andi Rafiyan (237006074), Arya Achmad Caesar (237006093)

## Matriks telaah

| Referensi | Kontribusi relevan | Metrik/fitur yang terlihat | Batasan untuk proyek |
|---|---|---|---|
| Polischuk, Proskurin, & Hryniuk (2025), [Machine-Learning-Based Selection of Encryption Algorithms for UAV](https://doi.org/10.18372/2410-7840.27.21186) | Paling dekat dengan tujuan seleksi algoritma berbasis ML. Merumuskan kriteria K1–K8; label dapat berupa algoritma terbaik atau kelas kelayakan. | Throughput, memori, ukuran blok/kunci, kebutuhan keamanan, perangkat, konteks misi. Mengusulkan label *optimal/acceptable/infeasible*. | Berfokus pada UAV dan kriteria pakar; bukan benchmark empiris persis pada empat algoritma proyek. Label rekomendasi berbasis aturan, bukan hanya hasil runtime. |
| Kumar & Goel (2025), [A Secure and Efficient Encryption System Based on Adaptive and Machine Learning for Securing Data in Fog Computing](https://doi.org/10.1038/s41598-025-92245-9) | Contoh sistem enkripsi adaptif dengan klasifikasi KNN. | Sensitivitas data; waktu enkripsi/dekripsi, throughput; ukuran data 1 KB, 100 KB, dan 1000 KB; memori dibahas sebagai aspek evaluasi. | Memilih AES atau hybrid ECC+AES menurut kategori data, bukan AES-128/AES-256/ChaCha20/3DES. Konteks fog dan data gambar/teks berbeda dari benchmark proyek. |
| Riatma et al. (2025), [Performance Evaluation and the Impact of File Size on Various AES Encryption Modes](https://doi.org/10.33795/jartel.v15i2.7323) | Acuan kuat untuk variasi ukuran file dan kontrol kondisi perangkat keras/perangkat lunak. | Membandingkan mode AES pada teks/gambar 1 KB–1000 KB; waktu enkripsi; ukuran file sebagai variabel. | Menguji mode AES, bukan algoritma target proyek; rentang ukuran lebih kecil dari target hingga 50 MB. |
| Buhari et al. (2025), [Performance and Security Analysis of Symmetric Data Encryption Algorithms: AES, 3DES and Blowfish](https://doi.org/10.35444/ijana.2025.16404) | Mendukung pemilihan AES dan 3DES sebagai algoritma yang dibandingkan. | Waktu eksekusi dan konsumsi memori disebut sebagai metrik; membahas aspek keamanan. | Tidak mencakup ChaCha20; detail mode/protokol dan konsistensi implementasi perlu diperiksa penuh sebelum mengadopsi prosedur. |
| Muhammed et al. (2024), [Comparative Analysis of AES, Blowfish, Twofish, Salsa20, and ChaCha20 for Image Encryption](https://doi.org/10.24017/science.2024.1.5) | Mendukung perbandingan AES dengan ChaCha20 dan keluarga stream cipher. | Studi enkripsi gambar; waktu/kecepatan dan throughput dibahas. | Domain gambar dapat memengaruhi interpretasi; algoritma, implementasi, dan mode tidak sepenuhnya sama dengan rancangan proyek. |
| Saydahd et al. (2025), [A Comparative Performance Evaluation of Hybrid Encryption Techniques Using ECC, RSA, AES, and ChaCha20 for Secure Data Transmission](https://doi.org/10.53523/ijoirvol12i2id598) | Konteks performa ChaCha20 dan AES pada lingkungan terbatas sumber daya. | Waktu enkripsi/dekripsi dan memori; berbagai tipe file. | Mengukur skema hybrid ECC/RSA + AES/ChaCha20, bukan cipher simetris secara terpisah. Gunakan sebagai konteks, bukan pembanding langsung. |
| Kshetri et al. (2024), [algoTRIC: Symmetric and Asymmetric Encryption Algorithms for Cryptography – A Comparative Analysis in AI Era](https://doi.org/10.14569/ijacsa.2024.0151201) | Gambaran umum perbandingan algoritma simetris/asimetris dan efisiensi. | Kecepatan pemrosesan, skalabilitas, kompleksitas, dan keamanan. | Cakupan luas; bukan rancangan ML adaptif atau benchmark yang langsung cocok dengan dataset proyek. Bobot metodologis lebih rendah. |

## Pengelompokan

### Referensi utama
- Polischuk et al. (2025): landasan seleksi algoritma berbasis ML, kriteria, dan pelabelan.
- Kumar & Goel (2025): contoh klasifikasi adaptif dan hubungan konteks dengan pilihan enkripsi.
- Riatma et al. (2025): rancangan variasi ukuran file dan pengukuran performa.
- Buhari et al. (2025): pembanding yang mencakup AES dan 3DES serta metrik performa.

### Artikel pendukung
- Muhammed et al. (2024): konteks komparasi AES dan ChaCha20 pada enkripsi gambar.
- Saydahd et al. (2025): konteks performa ChaCha20/AES pada skema hybrid.
- Kshetri et al. (2024): tinjauan komparatif umum.

## Kesimpulan Tahap 0

- Landasan utama seleksi ML: Polischuk et al. dan Kumar & Goel.
- Landasan benchmark ukuran/performa: Riatma et al. dan Buhari et al.
- Pendukung komparasi ChaCha20 dan gambaran umum: Muhammed et al., Saydahd et al., dan Kshetri et al.
- Belum ada satu paper yang mencakup tepat keempat algoritma proyek, rentang ukuran file, seluruh metrik, dan klasifikasi. Benchmark mandiri tetap diperlukan.

## Catatan metodologis untuk Tahap 1

Jangan gunakan `execution_time`, `cpu_usage`, `memory_usage`, atau `throughput` hasil enkripsi sebagai fitur prediksi sebelum algoritma dipilih. Metrik tersebut baru diketahui setelah eksekusi, sehingga pemakaiannya sebagai fitur pemilihan awal berisiko menimbulkan kebocoran target. Lebih tepat menggunakannya untuk membentuk label objektif atau mengevaluasi hasil. Fitur pemilihan awal sebaiknya berasal dari ukuran file dan kondisi sistem sebelum enkripsi.

## Batas telaah

Matriks ini merangkum isi yang dapat diperiksa dari artikel/abstrak dan ekstraksi PDF yang tersedia. Rincian protokol eksperimen setiap PDF belum seluruhnya diperiksa penuh. Tahap 0 memberi dasar untuk Tahap 1: tetapkan skema cipher yang aman dan sebanding, kondisi uji, jumlah pengulangan, lalu aturan label.
