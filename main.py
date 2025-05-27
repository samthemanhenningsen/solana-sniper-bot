import json
import time
import os
from solana.rpc.api import Client
from solana.publickey import PublicKey
from solana.keypair import Keypair
from dotenv import load_dotenv
from jupiter_python_sdk import JupiterApiClient, RoutePlan, QuoteResponse, TransactionResponse

load_dotenv()

# CONFIG
RPC_URL = os.getenv("RPC_URL")
WHALE_ADDRESS = "5bx3jhSVXcZGpGMNviTPaE2BWghUVToTH2UZnb3ZBs1tX"  # Replace with whale's wallet base58 pubkey
SLEEP_TIME = 5  # seconds between checks

client = Client(RPC_URL)

# Load your keypair
with open("wallet.json") as f:
    secret_key = json.load(f)
keypair = Keypair.from_secret_key(bytes(secret_key))
wallet_address = keypair.public_key

jupiter = JupiterApiClient()

def get_latest_transactions(pubkey: str, limit=5):
    sigs = client.get_signatures_for_address(PublicKey(pubkey), limit=limit)
    if not sigs["result"]:
        return []
    txs = []
    for sig_info in sigs["result"]:
        sig = sig_info["signature"]
        tx = client.get_transaction(sig, encoding="jsonParsed")
        if tx["result"]:
            txs.append(tx["result"])
    return txs

def mirror_trade(tx):
    try:
        # Step 1: Extract token mint from whale's transaction
        instructions = tx['transaction']['message']['instructions']
        token_mint = None
        for ix in instructions:
            if ix['program'] == 'spl-token':
                token_mint = ix['parsed']['info'].get('mint')
                break
        if not token_mint:
            print("No token mint found.")
            return

        print(f"[+] Token detected: {token_mint}")
        print("[*] Getting quote from Jupiter...")

        # Step 2: Get quote for buying the same token
        quote: QuoteResponse = jupiter.quote(
            input_mint="So11111111111111111111111111111111111111112",  # SOL mint
            output_mint=token_mint,
            amount=10000000,  # 0.01 SOL (adjust as needed)
            slippage_bps=50
        )

        route: RoutePlan = quote.best_route()
        tx: TransactionResponse = jupiter.swap(
            user_public_key=wallet_address,
            route_plan=route
        )
        tx.send(client, keypair)
        print("[+] Swap executed!")
    except Exception as e:
        print(f"[!] Error: {e}")

# MAIN LOOP
seen = set()
print(f"Bot started. Watching {WHALE_ADDRESS}...")
while True:
    try:
        txs = get_latest_transactions(WHALE_ADDRESS)
        for tx in txs:
            sig = tx['transaction']['signatures'][0]
            if sig not in seen:
                print(f"[TX] New transaction: {sig}")
                mirror_trade(tx)
                seen.add(sig)
        time.sleep(SLEEP_TIME)
    except KeyboardInterrupt:
        print("Exiting bot...")
        break
    except Exception as e:
        print(f"[!] Loop error: {e}")
        time.sleep(10)
