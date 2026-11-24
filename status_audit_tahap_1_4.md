# Status Audit Tahap 1–4

## Keputusan penutupan

Tahap 1–4 ditutup untuk eksperimen eksploratif sesuai `project_overview_workflow.md` beserta keputusan pengguna dalam `rencana_perbaikan_tahap_1_4.md`. Penutupan menyatakan kelengkapan metode dan artefak, bukan keberhasilan prediksi yang kuat. Tahap 5 (grafik, referensi hingga 20, laporan, PPT) belum dikerjakan oleh penutupan ini.

## Artefak aktif

- Data mentah aktif: `raw_dataset_cpu_corrected.csv` (720 baris / 180 putaran). Berkas ini adalah eksperimen baru, bukan modifikasi data historis.
- Data berlabel deskriptif utama: `labeled_dataset.csv`; salinan identik: `output_cpu_corrected/labeled_dataset_final.csv`.
- Pipeline aktif: `evaluate_models_final.py`.
- Hasil aktif: `output_cpu_corrected/evaluation_final.json`.
- Bukti pemeriksaan: `output_cpu_corrected/audit_checks.json`; pemeriksa dapat diulang dengan `py verify_final_audit.py`.
- Metadata: `metadata_lingkungan_perbaikan.md`; diagnostik CPU: `diagnostik_interval_cpu.json` dan `.csv`.
- Reproduksi kedua: `output_cpu_corrected_recheck/evaluation_final.json`, identik byte dengan laporan aktif.

## Pemetaan penerimaan

| Tahap / persyaratan | Artefak dan bukti | Status |
|---|---|---|
| 1: empat cipher, enam ukuran, seed, ulangan | `benchmark.py`: AES-128-CTR, AES-256-CTR, ChaCha20, 3DES-CTR; 1024–52428800 byte; seed 2026; 5 warmup dan 30 putaran | Terpenuhi |
| 1: kondisi sistem dan dokumentasi lingkungan | CPU aktual tanpa beban buatan sesuai keputusan pengguna; metadata hardware/runtime tercatat terpisah; overview dan rancangan diselaraskan | Terpenuhi melalui deviasi disetujui |
| 1: definisi pengukuran | CPU thread, waktu per enkripsi dalam batch >=1 detik, delta peak RSS sampling 10 ms; encrypt-only tanpa autentikasi | Terpenuhi; keterbatasan di bawah |
| 2: payload sintetis dan perulangan | `benchmark.py`; `tests/test_benchmark_core.py`, `tests/test_benchmark_smoke.py` | Terpenuhi |
| 2: data mentah lengkap dan terpisah | 720 baris, 180 putaran; empat algoritma tiap putaran; sumber baru dan historis memiliki hash tetap | Terpenuhi |
| 2: koreksi batas waktu CPU | Endpoint CPU sebelum penghentian sampler; diagnostik 36 pengukuran, ambang 1 poin persentase, maksimum 1.5624 poin; pengguna menyetujui benchmark ulang yang selesai exit 0 | Terpenuhi |
| 3: validasi dan penanganan calon anomali | Validasi numerik/group pada pipeline dan audit; pagar median-half IQR 1.5× per ukuran×algoritma, dipasang hanya pada train tiap fold | Terpenuhi |
| 3: label objektif dan throughput | Bobot 70/20/10, normalisasi dalam putaran, seri melalui throughput lalu nama algoritma; throughput dihitung ulang dari waktu olahan | Terpenuhi |
| 3: bukti perubahan, skor, label | `measurement_evidence.train/test` setiap split pada JSON: metrik before/after, penanda, trial, algoritma, ID, selection_score, optimal_algorithm; `bounds` menyimpan pagar | Terpenuhi |
| 3: dataset utama dan kelas | `labeled_dataset.csv` dipromosikan dari output baru sesudah backup byte-identik dataset lama; 68 AES-128, 54 AES-256, 58 ChaCha20; 3DES 0 | Terpenuhi |
| 4: split 80:20 dan K-Fold | 144 train / 36 holdout; lima fold hanya di 144 train, ukuran test 29/29/29/29/28; empat baris satu putaran tidak terpisah | Terpenuhi |
| 4: beberapa model termasuk pembanding | Decision Tree, Random Forest, Logistic Regression+StandardScaler train-only; parameter pada pipeline | Terpenuhi |
| 4: baseline if-else | Ambang ukuran dan kelas cabang dipilih dari train; opsi konstanta diperbolehkan; aturan tercatat per split | Terpenuhi |
| 4: metrik dan generalisasi | Accuracy, macro Precision/Recall/F1, confusion matrix, prediksi dan truth; pooled CV serta mean/std; leave-one-file-size-out tambahan | Terpenuhi |
| Audit: tidak bocor dan dapat direproduksi | Mutasi data test tidak mengubah bounds, scaler, baseline; holdout tidak masuk CV; 144 train diuji tepat sekali; metrik dihitung ulang; dua JSON identik byte | Terpenuhi |
| Audit: tes nyata | `py -m unittest discover -s tests -v`: 15 tes lulus; `py verify_final_audit.py`: PASS | Terpenuhi |

## Hasil yang digunakan

Metrik di bawah persen; macro-F1 dihitung dari gabungan prediksi, bukan rata-rata F1 antar-fold. Macro dihitung atas gabungan kelas aktual dan prediksi; kandidat yang tidak muncul diungkap terpisah, tidak ditambahkan sebagai suku nol diam-diam.

| Model | Akurasi CV (144 prediksi) | Macro-F1 CV | Akurasi holdout (36 prediksi) | Macro-F1 holdout |
|---|---:|---:|---:|---:|
| If-else | 22.2 | 20.9 | 41.7 | 19.6 |
| Decision Tree | 28.5 | 26.2 | 47.2 | 42.9 |
| Random Forest | 25.7 | 25.4 | 30.6 | 30.5 |
| Logistic Regression | 23.6 | 20.5 | 33.3 | 30.2 |

Hasil ukuran file tersisih: akurasi/F1 if-else 29.4/23.2; DT 32.8/24.9; RF 35.6/33.6; LR 27.8/23.8. Jangan tertukar dengan angka CV atau mengklaim keunggulan kuat berdasarkan selisih kecil.

## Deviasi disetujui dan batas interpretasi

1. Normal vs. loaded diganti pengukuran CPU aktual; tidak ada klaim kontrol beban atau sebab-akibat CPU. Empat algoritma berjalan berurutan, bukan pada kondisi identik. Fitur konteks adalah observasi sebelum algoritma pertama menurut trial.
2. CPU berarti rasio waktu CPU thread enkripsi, bukan CPU sistem puncak. Waktu meliputi loop pemanggilan enkripsi dalam batch; bukan biaya protokol end-to-end. Clock CPU dan wall tetap dipanggil berurutan, bukan atomik.
3. RSS diambil tiap 10 ms; lonjakan singkat bisa terlewat dan allocator dapat memengaruhi delta.
4. IQR menunjukkan calon anomali, bukan bukti proses OS tertentu. Winsorization memengaruhi label; label dihitung ulang lokal tiap fold dan tidak diasumsikan identik antar-fold.
5. Untuk ukuran yang tidak tersedia pada train, metrik dibiarkan mentah dan ditandai `unseen_stratum=true`. Throughput diturunkan ulang dengan formula yang sama; tidak ada pagar lintas ukuran.
6. Dataset deskriptif penuh memakai pagar full-data tetapi TIDAK digunakan sebagai sumber label evaluasi. Label evaluasi berasal dari raw dengan pagar train-only tiap split.
7. Tiga kelas target tidak membatalkan pengujian empat cipher. 3DES tidak dipaksakan menjadi pemenang; hasil ini bukan rekomendasi keamanan modern. Benchmark encrypt-only tidak menguji autentisitas/integritas.
8. Single-device, enam ukuran, 180 putaran, bukan validasi lintas perangkat. Hasil rendah dan berubah antar-skema; belum membuktikan selector ML andal.
9. Model/parameter tetap, tidak dipilih dengan menaikkan skor holdout. Evaluasi ukuran tersisih adalah analisis tambahan pada keseluruhan data, bukan validasi independen tambahan yang membenarkan tuning holdout.
10. Riwayat proyek sudah pernah mengevaluasi dataset lama dan melaporkan hasil holdout. Dokumentasi tidak mengklaim pengujian konfirmatori yang benar-benar buta atau belum pernah diperiksa.
11. Hardware diperiksa sekitar benchmark ulang; bukan rekonstruksi metadata historis. NumPy dan modul CSV stdlib menggantikan kebutuhan pandas untuk fungsi pengolahan tabel yang sama, tanpa perubahan metode. Pustaka visualisasi berada pada Tahap 5.

## Arsip dan nama sumber

`raw_dataset.csv` tetap mentah historis, tidak ditimpa agar sumber asli terjaga. Untuk memenuhi fungsi keluaran raw pada workflow, gunakan `raw_dataset_cpu_corrected.csv` sebagai sumber penelitian aktif. Perbedaan nama ini eksplisit, bukan menyajikan data lama sebagai hasil baru.

Dataset label historis disalin sebelum promosi ke `arsip_hasil_lama/labeled_dataset_sebelum_perbaikan.csv`, diverifikasi byte-identik. Skrip dan hasil historis lain tetap ada; daftar superseded ada pada `HASIL_AKTIF.md`.

Hash raw historis: `30ec8cc8859c4c2cadc58502e56fb1781f3467262e02d040ed900300f9c25188`.
Hash raw aktif: `b95ddcd73a6fd19cfcfc6190e9c693b3250baf1d5f4d8f56e6a7344be9091096`.

## Reproduksi

Dari folder proyek:

`py evaluate_models_final.py raw_dataset_cpu_corrected.csv output_cpu_corrected --expected-sha256 b95ddcd73a6fd19cfcfc6190e9c693b3250baf1d5f4d8f56e6a7344be9091096`

`py evaluate_models_final.py raw_dataset_cpu_corrected.csv output_cpu_corrected_recheck --expected-sha256 b95ddcd73a6fd19cfcfc6190e9c693b3250baf1d5f4d8f56e6a7344be9091096`

`py verify_final_audit.py`

`py -m unittest discover -s tests -v`

Perintah pertama dan kedua menghasilkan laporan identik. Jangan menjalankan benchmark baru untuk mencoba menaikkan akurasi; perubahan desain eksperimen perlu persetujuan baru.
