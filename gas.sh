#!/bin/bash

WALLET_FILE="wallet.txt"
PROXY_FILE="proxy.txt"
MAX_PARALLEL=10 # ⬅️ jumlah thread paralel, bisa disesuaikan

if [[ ! -f "$WALLET_FILE" || ! -f "$PROXY_FILE" ]]; then
  echo "wallet.txt atau proxy.txt tidak ditemukan!"
  exit 1
fi

paste "$WALLET_FILE" "$PROXY_FILE" | while IFS=$'\t' read -r wallet proxy; do
  # Jalankan proses di background
  echo "🚀 Claiming untuk wallet: $wallet dengan proxy: $proxy"
  node main.js "$wallet" "$proxy" &

  # Hitung jumlah proses paralel
  while [[ $(jobs -r -p | wc -l) -ge $MAX_PARALLEL ]]; do
    sleep 1
  done
done

# Tunggu semua proses selesai
wait
echo "✅ Semua proses selesai."
