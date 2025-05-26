# High-Speed Solana Whale Mirror Bot (Axiom Edition)
# Author: Orion for Sam
# Mirrors whale 2.b trades from Axiom and logs the behavior

import requests
from bs4 import BeautifulSoup
import time

# === CONFIGURATION ===
WHALE_NAME = "whale 2.b"
YOUR_WALLET = "FLyYbJNGu3AxDL1ULsyoWiKwo5e4tcMbsXpTQguwkT5t"
BUY_AMOUNT_SOL = 0.1

# Axiom live trade URL
AXIOM_URL = "https://axiom.trade/trackers"

# === MIRRORING FUNCTION ===
def scrape_whale_trades():
    print("🔥 Live scraping trades for whale 2.b from Axiom...\n")
    seen = set()

    while True:
        try:
            response = requests.get(AXIOM_URL)
            soup = BeautifulSoup(response.text, "html.parser")

            rows = soup.select("div:has(div:contains('whale 2.b'))")

            for row in rows:
                columns = row.find_all("div")

                if len(columns) < 3:
                    continue

                name = columns[0].text.strip()
                token = columns[1].text.strip()
                amount = columns[2].text.strip()
                sig = f"{token}:{amount}"

                if name.lower() != WHALE_NAME.lower():
                    continue

                if sig in seen:
                    continue

                seen.add(sig)

                # BUY/SELL classification by trade direction
                if "green" in row.get("class", []):
                    print(f"[BUY] Whale bought {token}. Mirroring...")
                    execute_buy(token)
                else:
                    print(f"[SELL] Whale sold {token}. Mirroring...")
                    execute_sell(token)

        except Exception as e:
            print("⚠️ Error scraping trades:", e)

        time.sleep(4)

# === EXECUTE BUY/SELL ===
def execute_buy(token):
    print(f"🟢 Simulated BUY for {token} with {BUY_AMOUNT_SOL} SOL on wallet {YOUR_WALLET}")

def execute_sell(token):
    print(f"🔴 Simulated SELL for {token} from wallet {YOUR_WALLET}")

# === MAIN ENTRY ===
if __name__ == "__main__":
    scrape_whale_trades()
