# Entertainment Hub

**Entertainment Hub** - Aplikasi yang berisikan hiburan, berupa film, series, musik, dll. 
Dibuat untuk tugas akhir mata kuliah Pemrograman Lanjut⭐

## Sekilas

![Screencapture](/Screencapture.png)

## Aplikasi Entertainment Hub memiliki kriteria :

1. Website ini bertema Hiburan dengan nama "Entertainment Hub" memiliki tampilan rekomendasi hiburan buat pengguna.
2. Website dibuat dengan Microframework Flask.
3. Memiliki Hak Akses yang berbeda antara Admin dan User biasa, dan password terengkripsi dengan Algoritma Secure Hash 256-bit (SHA256).
4. Memiliki Hak CRUD website hiburan ini untuk admin.
5. Database menggunakan sqlite.

## Scripts

1. Jalankan `pip install flask flask-sqlalchemy` untuk menginstal dependencies

2. Jalankan aplikasi dengan `python app.py`

3. Untuk dapatkan code supaya bisa mendaftar jadi admin, ganti URL rute menjadi `http://127.0.0.1:5000/get_admin_code`
