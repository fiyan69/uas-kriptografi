# Rencana Perbaikan dan Audit Final Tahap 1–4

## Acuan wajib

Selama perbaikan, gunakan bersama:
1. `project_overview_workflow.md`: persyaratan dan keluaran proyek.
2. `rencana_perbaikan_tahap_1_4.md` (dokumen ini): urutan perbaikan dan kriteria penerimaan.

Jangan menyatakan tahap selesai hanya karena skrip berjalan atau tes lulus. Petakan setiap persyaratan ke artefak dan pemeriksaan yang benar-benar dijalankan. Jangan lanjut ke Tahap 5 sebelum seluruh butir tertutup atau deviasi disetujui dan didokumentasikan. Bila dua acuan bertentangan, jelaskan konfliknya dan minta keputusan pengguna; jangan mengubah metodologi sepihak.

## Ruang lingkup dan status awal

Pelaksana: Andi Rafiyan (237006074), Arya Achmad Caesar (237006093).

Dokumen ini menyimpan rencana dan checklist yang telah ditutup berdasarkan bukti pada `status_audit_tahap_1_4.md` serta `output_cpu_corrected/audit_checks.json`. Bukan klaim akurasi tinggi; seluruh keterbatasan tetap berlaku.

Data mentah yang diperiksa sebelumnya: 720 baris, 180 putaran, enam ukuran, empat algoritma per putaran. Hash SHA-256 acuan `raw_dataset.csv`:

`30ec8cc8859c4c2cadc58502e56fb1781f3467262e02d040ed900300f9c25188`

Verifikasi kembali hash sebelum dan setelah perbaikan. Pertahankan berkas sumber asli; jangan mengoreksi angka pengukuran mentah secara retrospektif.

## 1. Kunci metodologi dan selaraskan dokumen

- [x] Pertahankan keputusan yang sudah disepakati: encrypt-only; CPU aktual tanpa klaim idle/loaded terkontrol; label per putaran; bobot waktu/CPU/memori 70/20/10.
- [x] Selaraskan `project_overview_workflow.md` dan `rancangan_tahap_1.md` melalui perubahan terdokumentasi; jangan menghapus jejak alasan deviasi.
- [x] Perjelas arahan lama tentang rentang CPU yang bertentangan dengan keputusan label per putaran. Jangan menambah pengelompokan CPU tanpa persetujuan baru.
- [x] Jelaskan bahwa label adalah pemenang performa/resource dalam putaran pada kondisi terukur, bukan bukti algoritma optimal pada tingkat CPU tertentu atau rekomendasi keamanan produksi.
- [x] Lengkapi model CPU, kapasitas RAM, storage, OS, versi Python, dan versi pustaka. Bedakan metadata yang terekam saat benchmark dari informasi perangkat yang baru diperiksa sekarang; tandai informasi historis yang tidak tersedia.
- [x] Jelaskan perbedaan CPU thread enkripsi dengan `cpu_delta`/`peak_cpu` dalam overview.

## 2. Periksa dampak kesalahan pengukuran CPU

- [x] Sejajarkan interval pengukuran waktu CPU dan waktu nyata dalam skrip; penghentian/join sampler tidak boleh hanya masuk salah satu interval.
- [x] Tetapkan prosedur uji pembanding dan cara menilai dampak sebelum menyimpulkan hasil.
- [x] Jalankan uji pembanding kecil; ukur dampak terhadap metrik, skor, dan label, bukan sekadar kelulusan skrip.
- [x] Bila dampak material ditemukan, jelaskan temuan dan diskusikan pengulangan benchmark dengan pengguna. Benchmark penuh tidak dijalankan ulang tanpa persetujuan.
- [x] Jika benchmark perlu diulang, simpan hasil sebagai eksperimen baru; data mentah lama tetap utuh. Jika tidak perlu diulang, dokumentasikan bukti dan keterbatasannya.

## 3. Tuntaskan preprocessing dan pelabelan

- [x] Validasi schema, nilai kosong, non-finite, nilai tidak valid, keunikan putaran, dan satu pengukuran tiap algoritma dalam setiap putaran.
- [x] Pertahankan semua empat baris satu putaran dalam partisi yang sama.
- [x] Hitung pagar IQR hanya dari train pada masing-masing split/fold, per ukuran file × algoritma; terapkan pagar yang sama ke test tanpa fitting ulang.
- [x] Jangan menganggap penanda IQR sebagai bukti kesalahan pengukuran atau mengklaim penyebabnya pasti proses OS.
- [x] Jika waktu diubah, hitung ulang throughput dengan satuan konsisten. Gunakan throughput yang konsisten sebagai pemecah skor seri.
- [x] Simpan penanda perubahan, pagar IQR, identitas putaran, skor, dan label setiap split/fold.
- [x] Tetapkan `labeled_dataset.csv` sebagai dataset deskriptif penuh. Evaluasi harus tetap dimulai dari raw dan memakai label hasil preprocessing lokal setiap split/fold, bukan label preprocessing global.
- [x] Catat kelas yang tidak terwakili. Jangan memaksa 3DES menang atau membuat sampel label buatan.

### Ukuran file yang tidak ada di train

Kebijakan telah disetujui pengguna: jangan koreksi metrik pada strata ukuran file yang belum tersedia di train; tandai `unseen_stratum=true` sebagai keterbatasan. Jangan menggunakan pagar waktu/memori lintas ukuran secara langsung karena efek ukuran dapat keliru dianggap outlier. Implementasi dan bukti ada pada `evaluate_models_final.py` serta JSON aktif. CV hanya pada 80% train juga telah disetujui; 20% holdout tidak masuk CV.

## 4. Lengkapi evaluasi

- [x] Jalankan Decision Tree, Random Forest, dan Logistic Regression sebagai pembanding tambahan yang diminta overview.
- [x] Untuk Logistic Regression, pasang standardisasi hanya pada train; jangan fitting scaler pada seluruh dataset.
- [x] Bandingkan baseline if-else; pilih ambang dan label cabang hanya dari train. Rekam aturan setiap split/fold.
- [x] Laporkan split 80:20, 5-fold, dan uji ukuran file tersisih sebagai evaluasi terpisah; uji ukuran tersisih bukan pengganti K-Fold.
- [x] Kunci protokol holdout: jika dipakai sebagai pengujian akhir independen, lakukan CV hanya pada bagian train dan jangan gunakan holdout untuk memilih model/parameter. Catat bahwa hasil holdout sebelumnya sudah pernah dilihat; jangan mengklaim data tersebut benar-benar belum pernah diperiksa.
- [x] Simpan indeks/identitas train dan test, prediksi per putaran, label aktual lokal fold, serta distribusi kelas.
- [x] Laporkan Accuracy, macro Precision, macro Recall, macro F1, dan Confusion Matrix dengan urutan kelas eksplisit. Jelaskan cara penggabungan prediksi antar-fold.
- [x] Pertahankan seed, parameter model, dan unit sampel yang jelas: satu sampel per putaran, bukan empat baris algoritma sebagai empat sampel independen.

## 5. Audit penutup

- [x] Pastikan hash data mentah sesuai acuan; sumber lama tidak tertimpa.
- [x] Uji bahwa empat algoritma tetap utuh dalam setiap putaran, train/test tidak tumpang tindih, dan setiap putaran muncul tepat satu kali sebagai test pada K-Fold.
- [x] Uji bahwa perubahan nilai test tidak mengubah pagar, scaler, atau aturan baseline yang dipasang pada train.
- [x] Uji konsistensi waktu–throughput, skor, label, dan perhitungan metrik dari prediksi tersimpan.
- [x] Jalankan ulang pipeline dari awal; buktikan hasil dapat direproduksi dan laporkan hasil eksekusi nyata.
- [x] Buat satu berkas status audit yang memetakan setiap persyaratan overview ke artefak dan bukti pemeriksaan; catat hal yang belum terpenuhi, deviasi disetujui, dan keterbatasan.
- [x] Tandai skrip/hasil lama sebagai superseded secara jelas tanpa menghapus sumber asli atau membuat pengguna keliru memilih hasil.

## Definisi final

Tahap 1–4 boleh dinyatakan final hanya jika semua persyaratan relevan memiliki bukti pemeriksaan, konflik dokumen terselesaikan, deviasi disetujui dan terdokumentasi, serta tidak ada kegagalan kritis yang belum ditangani. Akurasi tinggi bukan syarat kelulusan metodologi. Hasil rendah tetap dilaporkan apa adanya.

Jika suatu langkah membutuhkan keputusan baru atau pengulangan eksperimen besar, hentikan pada titik keputusan, jelaskan dampaknya, dan minta persetujuan pengguna sebelum melanjutkan.
