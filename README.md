# Evaluasi Klasifikasi Machine Learning untuk Pemilihan Enkripsi Dinamis

Proyek PBL Kriptografi: menguji AES-128-CTR, AES-256-CTR, ChaCha20, dan 3DES-CTR pada berbagai ukuran file, lalu mengevaluasi apakah model machine learning dapat memilih algoritma berdasarkan performa pengukuran.

## Mulai

```bash
py evaluate_models_final.py
py buat_grafik_eksperimen.py
```

Benchmark baru dijalankan dengan hati-hati karena membutuhkan waktu:

```bash
py benchmark.py --output raw_dataset_cpu_corrected.csv --sizes 1024 10240 102400 1048576 10485760 52428800 --repeats 30 --warmups 5 --seed 2026
```

## Acuan utama

- `project_overview_workflow.md`: alur dan spesifikasi proyek.
- `status_audit_tahap_1_4.md`: status audit tahap 1–4.
- `HASIL_AKTIF.md`: daftar artefak hasil aktif.
- `grafik_hasil_eksperimen/PANDUAN_GRAFIK.md`: sumber dan cara membaca grafik.

## Catatan hasil

Evaluasi bersifat eksploratif. Model machine learning belum konsisten mengungguli baseline sederhana. Hasil tidak boleh ditafsirkan sebagai bukti keamanan kriptografi; penelitian ini membandingkan performa dan pemilihan algoritma berdasarkan data benchmark.
