from web3 import Web3
from web3.types import ChecksumAddress
from pathlib import Path

from .errors import InvalidAddressException

def validate_address(
    address: str
) -> ChecksumAddress:
    if not Web3.is_address(address):
        raise InvalidAddressException(f"Invalid address for {address}")

    return Web3.to_checksum_address(address)

def validate_directory(
    directory: Path
) -> Path:
    if not directory.is_dir():
        raise FileNotFoundError("Directory does not exist")
    return directory
