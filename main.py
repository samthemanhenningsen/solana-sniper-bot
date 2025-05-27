# High-Speed Solana Whale Mirror Bot (Axiom Edition)
# Author: Orion for Sam

import requests
from bs4 import BeautifulSoup
import time

# === CONFIGURATION ===
WHALE_NAME = "whale 2.b"
from solana.keypair import Keypair
import json

# Load your real wallet from wallet.json
with open("wallet.json") as f:
    secret_key = json.load(f)
    keypair = Keypair.from_secret_key(bytes(secret_key))
    YOUR_WALLET = str(keypair.public_key)

BUY_AMOUNT_SOL = 0.1
AXIOM_URL = "https://axiom.trade/trackers"

# === MIRRORING FUNCTION ===
def scrape_whale_trades():
    print("🔥 Live scraping trades for whale 2.b from Axiom...\n")
    seen = set()

    while True:
        try:
            response = requests.get(AXIOM_URL)
            soup = BeautifulSoup(response.text, "html.parser")

            rows = soup.find_all("div", string=lambda t: t and "whale 2.b" in t)

            for row in rows:
                parent = row.find_parent("div")
                siblings = parent.find_all("div")

                if len(siblings) < 3:
                    continue

                name = siblings[0].text.strip()
                token = siblings[1].text.strip()
                amount = siblings[2].text.strip()
                sig = f"{token}:{amount}"

                if name.lower() != WHALE_NAME.lower():
                    continue

                if sig in seen:
                    continue

                seen.add(sig)

                if float(amount) % 2 > 1:
                    print(f"[BUY] Whale bought {token}. Mirroring...")
                    execute_buy(token)
                else:
                    print(f"[SELL] Whale sold {token}. Mirroring...")
                    execute_sell(token)

        except Exception as e:
            print("⚠️ Error scraping trades:", e)

        time.sleep(4)

def execute_buy(token):
    print(f"🟢 Simulated BUY for {token} with {BUY_AMOUNT_SOL} SOL on wallet {YOUR_WALLET}")

def execute_sell(token):
    print(f"🔴 Simulated SELL for {token} from wallet {YOUR_WALLET}")

# === START SCRIPT ===
if __name__ == "__main__":
    scrape_whale_trades()
