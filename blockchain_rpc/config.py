import os
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY         = os.getenv("PRIVATE_KEY")

TESTNET_ENDPOINT    = os.getenv("TESTNET_ENDPOINT")
TO_ADDRESS          = os.getenv("TO_ADDRESS")

ENDPOINT_1          = os.getenv("ENDPOINT_1")
SWAP_ADDRESS_1      = os.getenv("SWAP_ADDRESS_1")
COIN_1_ADDRESS_1    = os.getenv("COIN_1_ADDRESS_1")
COIN_2_ADDRESS_1    = os.getenv("COIN_2_ADDRESS_1")

ENDPOINT_2          = os.getenv("ENDPOINT_2")
SWAP_ADDRESS_2      = os.getenv("SWAP_ADDRESS_2")
COIN_1_ADDRESS_2    = os.getenv("COIN_1_ADDRESS_2")
COIN_2_ADDRESS_2    = os.getenv("COIN_2_ADDRESS_2")
