# Sanubot - Telegram AI Bot

Bot Telegram ini terintegrasi dengan OpenRouter menggunakan model `NVIDIA: Nemotron 3 Nano Omni (Free)`.

## Cara Penggunaan / Instalasi Lokal:
1. Ekstrak file zip ini.
2. Buka file `.env` dan isi token Telegram serta OpenRouter API Key Anda.
3. Install dependensi: `pip install -r requirements.txt`
4. Jalankan bot: `python bot.py`

## Cara Deploy ke GitHub & Render:
1. Buat repository baru di GitHub.
2. Inisialisasi git pada folder ini, commit, dan push ke GitHub Anda.
   *(Jangan khawatir, file `.env` otomatis diabaikan karena sudah ada `.gitignore` sejak awal).*
3. Di Render, buat **Background Worker**, sambungkan ke GitHub Anda.
4. Set Build Command: `pip install -r requirements.txt`
5. Set Start Command: `python bot.py`
6. Masukkan isi `.env` ke dalam **Environment Variables** di dashboard Render.
