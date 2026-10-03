#!/usr/bin/env python3
"""
Stellar CLI Tool
------------------
CLI sederhana untuk mengelola akun Stellar testnet.
"""
import argparse
import sys

import requests
from stellar_sdk import Keypair, Server

BASE_URL = "https://horizon-testnet.stellar.org"
FRIENDBOT_URL = "https://friendbot.stellar.org"


def cmd_create(args):
    """Generate random Stellar keypair, print results, and request testnet coins."""
    keypair = Keypair.random()
    public_key = keypair.public_key
    secret_key = keypair.secret

    print("=== Stellar Keypair (Testnet) ===")
    print("Public Key : " + public_key)
    print("Secret Key : " + secret_key)

    url = FRIENDBOT_URL + "?addr=" + public_key
    print("")
    print("Mencoba minta koin testnet dari " + url + " ...")

    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            try:
                data = resp.json()
            except ValueError:
                print("[GAGAL] Response dari Friendbot bukan JSON valid.")
                print("  Response: " + resp.text[:300])
                return 1

            print("[OK] Koin testnet berhasil didapatkan!")
            print("  Account ID : " + str(data.get("account_id")))
            print("  Sequence   : " + str(data.get("sequence")))
            print("  Balance XLM: " + str(data.get("balance")))
        else:
            err = data.get("detail") or data.get("title") or "unknown"
            print("[GAGAL] Friendbot: " + err)
            doc = data.get("document") or {}
            print("  Detail    : " + str(doc.get("error", err)))
            print("  Response: " + resp.text[:300])
    except requests.exceptions.RequestException as e:
        print("[GAGAL] Gagal terhubung ke Friendbot: " + str(e))
        print("  (Anda masih bisa pakai akun ini di CLI ini.)")

    return 0


def cmd_balance(args):
    """Check XLM balance from Horizon Testnet."""
    try:
        resp = requests.get(BASE_URL + "/accounts/" + args.address, timeout=30)
    except requests.exceptions.RequestException as e:
        print("[GAGAL] Gagal terhubung ke Horizon Testnet: " + str(e))
        return 1

    if resp.status_code == 404:
        print("[GAGAL] Akun '" + args.address + "' tidak ditemukan di Horizon Testnet.")
        return 1

    try:
        data = resp.json()
    except ValueError:
        print("[GAGAL] Response dari Horizon Testnet bukan JSON valid.")
        print("  Response: " + resp.text[:300])
        return 1

    account = data.get("account") or {}
    balance = account.get("balance")
    thresholds = account.get("thresholds") or []
    subentry = account.get("subentry_count")

    print("=== Saldo XLM (Testnet) ===")
    print("Alamat     : " + str(account.get("address")))
    print("Saldo XLM  : " + str(balance))
    print("Thresholds : " + str(thresholds))
    print("Subentry   : " + str(subentry))

    if subentry in (None, 0):
        print("Hak akses: PRIVATE (akun belum diakses pengguna lain).")

    return 0


def cmd_send(args):
    """Send native asset (XLM) on Stellar testnet."""
    try:
        source = Keypair.from_secret(args.secret_pengirim)
    except Exception as e:
        print("[GAGAL] Secret key pengirim tidak valid: " + str(e))
        return 1

    destination = args.public_tujuan
    try:
        amount = str(float(args.jumlah))
    except ValueError:
        print("[GAGAL] Jumlah harus berupa angka (misal: 10.5).")
        return 1

    print("=== Transfer XLM (Testnet) ===")
    print("Dari     : " + source.public_key)
    print("Kepada   : " + destination)
    print("Jumlah   : " + amount + " XLM")
    print("[OK] Konfigurasi diterima. Membuat transaction...")

    try:
        server = Server(BASE_URL)
        source_account = server.accounts().account_id(source.public_key).call()
    except requests.exceptions.RequestException as e:
        print("[GAGAL] Gagal mengambil info akun sumber: " + str(e))
        return 1

    transaction = server.transactions().build()

    try:
        transaction.append_pay_op(
            destination=destination,
            amount=amount,
            asset="XLM",
        )
    except Exception as e:
        print("[GAGAL] Gagal menyusun operasi transfer: " + str(e))
        return 1

    try:
        transaction.sign(source)
    except Exception as e:
        print("[GAGAL] Gagal menandatangani transaction: " + str(e))
        return 1

    try:
        resp = transaction.submit()
    except requests.exceptions.RequestException as e:
        print("[GAGAL] Gagal mengirim ke Horizon Testnet: " + str(e))
        return 1

    if resp.status_code == 200:
        try:
            result = resp.json()
        except ValueError:
            print("[GAGAL] Response dari Horizon Testnet bukan JSON valid.")
            print("  Response: " + resp.text[:300])
            return 1
        print("[OK] Transaction berhasil dikirim!")
        print("  Hash       : " + str(result.get("id")))
        print("  Status     : " + str(result.get("status")))
        print("  Explore    : https://horizon-testnet.stellar.org/tx/" + str(result.get("id")))
    else:
        print("[GAGAL] Gagal mengirim transaction (HTTP " + str(resp.status_code) + ").")
        print("  Response: " + resp.text[:500])

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Stellar CLI Tool - kelola akun Stellar testnet dengan mudah.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="Stellar CLI Tool 1.0.0",
    )

    sub = parser.add_subparsers(dest="command", help="Perintah yang tersedia")

    p_create = sub.add_parser("create", help="Buat keypair baru dan minta koin testnet")
    p_create.set_defaults(func=cmd_create)

    p_balance = sub.add_parser("balance", help="Cek saldo XLM dari Horizon Testnet")
    p_balance.add_argument("address", help="Alamat Stellar (public key) yang mau dicek")
    p_balance.set_defaults(func=cmd_balance)

    p_send = sub.add_parser("send", help="Kirim XLM ke akun lain di testnet")
    p_send.add_argument("secret_pengirim", help="Secret key akun pengirim")
    p_send.add_argument("public_tujuan", help="Public key akun penerima")
    p_send.add_argument("jumlah", help="Jumlah XLM yang ingin dikirim (misal: 10.5)")
    p_send.set_defaults(func=cmd_send)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
