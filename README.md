# Setup

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

## Listen and Send

python3 -m blockchain_rpc listenAndSend 0.001 10

## Arbitrage

python3 -m blockchain_rpc arbitrage 500
