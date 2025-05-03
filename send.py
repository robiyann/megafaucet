from web3 import Web3
from eth_account import Account
import time
import random
from math import ceil
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Konfigurasi ---
RPC_URL = "https://carrot.megaeth.com/rpc"
CHAIN_ID = 6342
GAS_LIMIT = 21000
GAS_PRICE_GWEI = 1

eth_to_send = float(input("Jumlah ETH yang akan dikirim per wallet (misal 0.001): "))
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# --- Load Private Keys & Receiver Addresses ---
with open("pk.txt", "r") as f:
    private_keys = [line.strip() for line in f if line.strip()]

with open("address.txt", "r") as f:
    receivers = [line.strip() for line in f if line.strip()]

if not private_keys or not receivers:
    raise Exception("File pk.txt atau address.txt kosong.")

print(f"\nTotal wallet pengirim (sebelum validasi): {len(private_keys)}")
print(f"Total wallet penerima            : {len(receivers)}")
print("\n⏳ Memeriksa saldo wallet...\n")

# --- Cek Saldo Wallet Secara Paralel ---
def check_wallet(pk, idx):
    try:
        acct = Account.from_key(pk)
        balance = w3.eth.get_balance(acct.address)
        value_wei = w3.to_wei(eth_to_send, 'ether')
        gas_price = w3.to_wei(GAS_PRICE_GWEI, 'gwei')
        total_cost = value_wei + gas_price * GAS_LIMIT
        if balance >= total_cost:
            return (idx, pk)
    except:
        return None

valid_wallets = []
with ThreadPoolExecutor(max_workers=30) as executor:
    futures = [executor.submit(check_wallet, pk, idx) for idx, pk in enumerate(private_keys)]
    for future in as_completed(futures):
        result = future.result()
        if result:
            valid_wallets.append(result)

if not valid_wallets:
    print("❌ Tidak ada wallet dengan saldo cukup.")
    exit()

print(f"✅ Wallet yang valid untuk dikirim: {len(valid_wallets)}")

# --- Distribusi Wallet ke Penerima Secara Merata ---
random.shuffle(valid_wallets)
chunk_size = ceil(len(valid_wallets) / len(receivers))
chunks = [valid_wallets[i:i + chunk_size] for i in range(0, len(valid_wallets), chunk_size)]

# --- Fungsi Pengiriman ETH ---
def send_eth(pk, receiver, idx):
    try:
        acct = Account.from_key(pk)
        address = acct.address
        value_wei = w3.to_wei(eth_to_send, 'ether')
        gas_price = w3.to_wei(GAS_PRICE_GWEI, 'gwei')
        nonce = w3.eth.get_transaction_count(address)

        tx = {
            'nonce': nonce,
            'to': receiver,
            'value': value_wei,
            'gas': GAS_LIMIT,
            'gasPrice': gas_price,
            'chainId': CHAIN_ID
        }

        signed_tx = acct.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        return f"[{idx}] {address} ✅ TX terkirim: {tx_hash.hex()}"
    except Exception as e:
        return f"[{idx}] {address} ❌ ERROR: {str(e)}"

# --- Kirim ETH Secara Paralel ---
print("\n🚀 Mengirim transaksi...\n")
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = []
    for i, (receiver, chunk) in enumerate(zip(receivers, chunks)):
        print(f"--- Group {i+1}: Kirim ke {receiver} ({len(chunk)} wallet) ---")
        for idx, pk in chunk:
            futures.append(executor.submit(send_eth, pk, receiver, idx))

    for future in as_completed(futures):
        print(future.result())
