# Metadata Lingkungan dan Status Perbaikan

## Sumber dan batas klaim

Informasi berikut dibaca dari perangkat di sekitar pelaksanaan benchmark ulang. Bukan rekonstruksi konfigurasi hardware benchmark lama. OS, Python, dan versi pustaka pada dataset historis tetap mengikuti kolom yang terekam di CSV historis. Metadata saat ini tidak menggantikan nilai historis yang tidak tersedia.

## Perangkat dan runtime

- Produsen/model: Axioo Pongo 725.
- CPU: 12th Gen Intel(R) Core(TM) i7-12650H; 10 core fisik, 16 logical processor (Windows CIM).
- Memori fisik dilaporkan OS: 25442508800 byte. Jangan menggantinya dengan spesifikasi profil pengguna atau mengklaim kapasitas modul terpasang tanpa pemeriksaan tambahan.
- Storage model: INTEL SSDPEKNW512G8H; ukuran dilaporkan Windows CIM 512105932800 byte.
- OS: Windows-11-10.0.26200-SP0.
- Python: 3.12.10 (`py`).
- PyCryptodome: 4.5.0.
- psutil: 7.2.2.
- scikit-learn: 1.9.1.
- NumPy: 2.2.6.
- Waktu pemeriksaan runtime: 2026-11-23T10:15:20.785134+00:00.
- Sumber perangkat: `Get-CimInstance Win32_Processor`, `Win32_ComputerSystem`, `Win32_DiskDrive`; runtime memakai Python `platform`, pustaka terpasang, dan `psutil`.

## Diagnostik interval CPU

- Skrip: `diagnostik_interval_cpu.py`.
- Hasil: `diagnostik_interval_cpu.csv` dan `diagnostik_interval_cpu.json`.
- 36 pengukuran, 9 putaran; ukuran 1 KB, 1 MB, 50 MB; perbandingan interval lama dan interval diperbaiki pada pekerjaan enkripsi yang sama.
- Ambang diagnostik ditetapkan sebelum eksekusi: tambahan >=1 poin persentase CPU atau perubahan pemenang putaran.
- Tambahan CPU maksimum akibat penghentian sampler: 1.5623987565605748 poin persentase; tidak ada perubahan pemenang pada 9 putaran diagnostik.
- Tidak dapat merekonstruksi overhead historis; uji kecil tanpa warmup bukan pembuktian bahwa semua label historis tidak terdampak.
- `benchmark.py` kini mengambil akhir waktu CPU sebelum penghentian/join sampler. Empat tes benchmark lulus sebelum benchmark ulang dimulai.

## Keputusan pengguna dan benchmark ulang

Pengguna menyetujui:
1. Ukuran file yang tidak tersedia pada train dibiarkan mentah saat uji, diberi penanda tidak dikoreksi; tanpa pagar lintas ukuran.
2. CV hanya pada 80% bagian train; 20% holdout tidak masuk CV. Data historis yang pernah dievaluasi tidak disebut data yang belum pernah diperiksa.
3. Benchmark penuh diulang dengan interval CPU diperbaiki, disimpan ke raw baru; dataset historis dipertahankan.

Perintah benchmark ulang:

`py benchmark.py --output raw_dataset_cpu_corrected.csv --sizes 1024 10240 102400 1048576 10485760 52428800 --repeats 30 --warmups 5 --seed 2026`

Benchmark ulang (`proc_ead0759dbed0`) selesai normal exit 0; 720 baris / 180 putaran diverifikasi. SHA-256 raw aktif: `b95ddcd73a6fd19cfcfc6190e9c693b3250baf1d5f4d8f56e6a7344be9091096`. Evaluasi dan audit penutup ada di `status_audit_tahap_1_4.md`. Jangan menjalankan pelatihan/evaluasi berat bersamaan dengan pengumpulan benchmark berikutnya.

Raw lama tetap `raw_dataset.csv`, SHA-256 acuan:
`30ec8cc8859c4c2cadc58502e56fb1781f3467262e02d040ed900300f9c25188`.

Ikuti `project_overview_workflow.md` bersama `rencana_perbaikan_tahap_1_4.md`; status final menunggu seluruh penerimaan diverifikasi.
