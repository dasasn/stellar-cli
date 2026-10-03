# Stellar CLI Tool

CLI sederhana untuk mengelola akun Stellar di **testnet**. Cocok untuk submit hackathon.

## Fitur

- `create` — generate random Stellar keypair, cetak public key & secret key, lalu otomatis minta koin testnet dari Friendbot.
- `balance <address>` — cek saldo XLM dari Horizon Testnet.
- `send <secret> <destination> <amount>` — kirim native asset XLM di testnet.

## Install Requirements

```bash
pip install -r requirements.txt
```

Isi `requirements.txt`:

```txt
stellar-sdk
requests
```

## Jalankan

```bash
python stellar_cli.py create
python stellar_cli.py balance <alamat_stellar>
python stellar_cli.py send <secret_pengirim> <public_tujuan> <jumlah>
```

Contoh:

```bash
python stellar_cli.py create
python stellar_cli.py balance GCVS...
python stellar_cli.py send SD3OOK...  GCVO... 10.5
```

> Catatan: koin testnet dari Friendbot bersifat gratis dan tidak bernilai nyata. Jangan bagikan secret key dengan siapa pun.
