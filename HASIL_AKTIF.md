# Hasil Aktif dan Arsip

## Gunakan untuk Tahap 5

- Acuan: `project_overview_workflow.md` + `rencana_perbaikan_tahap_1_4.md`.
- Status dan keterbatasan: `status_audit_tahap_1_4.md`.
- Metadata: `metadata_lingkungan_perbaikan.md`.
- Raw aktif: `raw_dataset_cpu_corrected.csv`.
- Label deskriptif utama: `labeled_dataset.csv`.
- Pipeline: `evaluate_models_final.py`.
- Laporan: `output_cpu_corrected/evaluation_final.json`.
- Bukti audit: `output_cpu_corrected/audit_checks.json`, `verify_final_audit.py`.
- Bukti per-fold: bagian `measurement_evidence`, `bounds`, `baseline_rule`, `logistic_scaler`, IDs, truth dan predictions pada JSON aktif.

## Superseded: jangan kutip sebagai hasil akhir

`raw_dataset.csv` merupakan raw historis interval CPU lama, dipertahankan utuh; bukan raw aktif.
`evaluate_models.py`, `evaluate_models_leakage_safe.py`, `preprocess_dataset.py`, `model_evaluation.json`, `model_evaluation_leakage_safe.json`, `preprocessed_dataset.csv`, `preprocessed_dataset_descriptive.csv`, `labeled_dataset_preprocessed.csv`, serta `output_final/` merupakan versi historis/provisional.
`output_cpu_corrected_recheck/` adalah bukti reproduksi, bukan eksperimen berbeda.
Semua pilot/check CSV adalah pengujian awal, bukan dataset utama.
Label utama lama tersimpan pada `arsip_hasil_lama/labeled_dataset_sebelum_perbaikan.csv`; salinan diverifikasi sebelum promosi.

Tidak ada raw historis atau referensi asli yang dihapus. `label_dataset.py` tetap utilitas historis; jangan menjalankannya pada raw lama untuk mengganti label utama baru.
