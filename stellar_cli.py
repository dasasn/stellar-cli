#!/usr/bin/env python3

"""
Stellar CLI Tool
================
CLI sederhana untuk mengelola akun Stellar Testnet.

Perintah:
    python stellar.py create
    python stellar.py balance G...
    python stellar.py send S... G... 10
"""

import argparse
import sys
from decimal import Decimal, InvalidOperation

import requests
from stellar_sdk import (
    Asset,
    Keypair,
    Network,
    Server,
    TransactionBuilder,
)


BASE_URL = "https://horizon-testnet.stellar.org"
FRIENDBOT_URL = "https://friendbot.stellar.org"


# ============================================================
# CREATE ACCOUNT + FRIENDBOT
# ============================================================

def cmd_create(args):
    """Membuat keypair baru dan meminta XLM Testnet."""

    keypair = Keypair.random()

    public_key = keypair.public_key
    secret_key = keypair.secret

    print()
    print("=== Stellar Keypair (Testnet) ===")
    print("Public Key : " + public_key)
    print("Secret Key : " + secret_key)
    print()

    print("Meminta XLM Testnet dari Friendbot...")

    try:
        response = requests.get(
            FRIENDBOT_URL,
            params={"addr": public_key},
            timeout=30,
        )
    except requests.RequestException as e:
        print()
        print("[GAGAL] Tidak dapat terhubung ke Friendbot.")
        print("Error:", e)
        return 1

    print("HTTP Status:", response.status_code)

    if response.status_code != 200:
        print()
        print("[GAGAL] Friendbot menolak request.")

        try:
            error_data = response.json()
            print("Response:")
            print(error_data)
        except ValueError:
            print("Response:")
            print(response.text[:1000])

        return 1

    try:
        data = response.json()
    except ValueError:
        print()
        print("[GAGAL] Response Friendbot bukan JSON.")
        print(response.text[:1000])
        return 1

    print()
    print("[OK] Akun berhasil dibuat dan mendapat XLM Testnet.")
    print("Account ID : " + str(data.get("account_id")))
    print("Sequence   : " + str(data.get("sequence")))
    print("Balance    : " + str(data.get("balance")) + " XLM")
    print()

    print("SIMPAN SECRET KEY DENGAN AMAN.")
    print("Jangan kirim Secret Key kepada siapa pun.")

    return 0


# ============================================================
# CHECK BALANCE
# ============================================================

def cmd_balance(args):
    """Melihat saldo akun Stellar Testnet."""

    address = args.address.strip()

    try:
        response = requests.get(
            BASE_URL + "/accounts/" + address,
            timeout=30,
        )
    except requests.RequestException as e:
        print("[GAGAL] Tidak dapat terhubung ke Horizon Testnet.")
        print("Error:", e)
        return 1

    if response.status_code == 404:
        print("[GAGAL] Akun tidak ditemukan di Stellar Testnet.")
        print("Alamat:", address)
        return 1

    if response.status_code != 200:
        print("[GAGAL] Horizon mengembalikan HTTP", response.status_code)
        print(response.text[:1000])
        return 1

    try:
        data = response.json()
    except ValueError:
        print("[GAGAL] Response Horizon bukan JSON.")
        print(response.text[:1000])
        return 1

    print()
    print("=== Saldo Stellar Testnet ===")
    print("Alamat      :", data.get("account_id"))
    print("Sequence    :", data.get("sequence"))
    print("Subentries  :", data.get("subentry_count"))

    balances = data.get("balances", [])

    if not balances:
        print("Saldo       : 0")
        return 0

    print()
    print("Balances:")

    for balance in balances:
        asset_type = balance.get("asset_type")

        if asset_type == "native":
            print(
                "XLM         :",
                balance.get("balance")
            )
        else:
            print(
                balance.get("asset_code"),
                ":",
                balance.get("balance")
            )

    return 0


# ============================================================
# SEND XLM
# ============================================================

def cmd_send(args):
    """Mengirim XLM pada Stellar Testnet."""

    secret = args.secret_pengirim.strip()
    destination = args.public_tujuan.strip()

    # --------------------------------------------------------
    # Validasi secret
    # --------------------------------------------------------

    try:
        source_keypair = Keypair.from_secret(secret)
    except Exception as e:
        print("[GAGAL] Secret Key tidak valid.")
        print("Error:", e)
        return 1

    # --------------------------------------------------------
    # Validasi jumlah
    # --------------------------------------------------------

    try:
        amount_decimal = Decimal(args.jumlah)

        if amount_decimal <= 0:
            raise InvalidOperation

        # Stellar maksimal 7 angka desimal
        if amount_decimal.as_tuple().exponent < -7:
            print("[GAGAL] Jumlah XLM maksimal 7 angka desimal.")
            return 1

        amount = format(amount_decimal, "f")

    except (InvalidOperation, ValueError):
        print("[GAGAL] Jumlah XLM tidak valid.")
        print("Contoh: 10 atau 10.5")
        return 1

    # --------------------------------------------------------
    # Validasi destination
    # --------------------------------------------------------

    try:
        Keypair.from_public_key(destination)
    except Exception as e:
        print("[GAGAL] Public Key tujuan tidak valid.")
        print("Error:", e)
        return 1

    # --------------------------------------------------------
    # Tampilkan informasi
    # --------------------------------------------------------

    print()
    print("=== Transfer XLM Testnet ===")
    print("Dari   :", source_keypair.public_key)
    print("Kepada :", destination)
    print("Jumlah :", amount, "XLM")
    print()

    # --------------------------------------------------------
    # Hubungkan Horizon
    # --------------------------------------------------------

    try:
        server = Server(horizon_url=BASE_URL)

        source_account = server.load_account(
            source_keypair.public_key
        )

    except Exception as e:
        print("[GAGAL] Tidak dapat mengambil akun sumber.")
        print("Pastikan akun sudah dibuat/funded di Testnet.")
        print("Error:", e)
        return 1

    # --------------------------------------------------------
    # Build transaction
    # --------------------------------------------------------

    try:
        transaction = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
                base_fee=100,
            )
            .append_payment_op(
                destination=destination,
                amount=amount,
                asset=Asset.native(),
            )
            .set_timeout(30)
            .build()
        )

    except Exception as e:
        print("[GAGAL] Tidak dapat membuat transaction.")
        print("Error:", e)
        return 1

    # --------------------------------------------------------
    # Sign
    # --------------------------------------------------------

    try:
        transaction.sign(source_keypair)

    except Exception as e:
        print("[GAGAL] Transaction gagal ditandatangani.")
        print("Error:", e)
        return 1

    # --------------------------------------------------------
    # Submit
    # --------------------------------------------------------

    print("Mengirim transaction ke Stellar Testnet...")

    try:
        result = server.submit_transaction(transaction)

    except Exception as e:
        print()
        print("[GAGAL] Transaction ditolak oleh Horizon.")
        print("Error:")
        print(e)
        return 1

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    print()
    print("[OK] Transaction berhasil!")
    print("Hash   :", result.get("hash"))
    print("Ledger :", result.get("ledger"))
    print()
    print(
        "Explorer:"
    )
    print(
        "https://stellar.expert/explorer/testnet/tx/"
        + str(result.get("hash"))
    )

    return 0


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description="Stellar CLI Tool - Stellar Testnet"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Stellar CLI Tool 2.0.0",
    )

    subparsers = parser.add_subparsers(
        dest="command"
    )

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    create_parser = subparsers.add_parser(
        "create",
        help="Buat akun baru dan minta XLM Testnet",
    )

    create_parser.set_defaults(
        func=cmd_create
    )

    # --------------------------------------------------------
    # BALANCE
    # --------------------------------------------------------

    balance_parser = subparsers.add_parser(
        "balance",
        help="Cek saldo akun Stellar Testnet",
    )

    balance_parser.add_argument(
        "address",
        help="Public Key Stellar (G...)",
    )

    balance_parser.set_defaults(
        func=cmd_balance
    )

    # --------------------------------------------------------
    # SEND
    # --------------------------------------------------------

    send_parser = subparsers.add_parser(
        "send",
        help="Kirim XLM Testnet",
    )

    send_parser.add_argument(
        "secret_pengirim",
        help="Secret Key pengirim (S...)",
    )

    send_parser.add_argument(
        "public_tujuan",
        help="Public Key penerima (G...)",
    )

    send_parser.add_argument(
        "jumlah",
        help="Jumlah XLM, contoh: 10 atau 10.5",
    )

    send_parser.set_defaults(
        func=cmd_send
    )

    # --------------------------------------------------------
    # EXECUTE
    # --------------------------------------------------------

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
