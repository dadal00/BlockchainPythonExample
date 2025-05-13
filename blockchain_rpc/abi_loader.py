import json
from pathlib import Path
from typing import Any, Dict, Optional

from .utils import validate_directory
from .models import ABI
from .errors import ABIException

class ABILoader:
    """
    Responsible for loading in and lending out available ABIs.

    Attributes
    ------------
    _abi_dir: :class:`Path`
        Optional Path to directory for ABIs.
    _abis: :class:`Dict[str, Any]`
        The ABIs loaded in as a python dictionary.
    """
    def __init__(
        self, 
        abi_directory: Optional[Path] = Path('./blockchain_rpc/abi')
    ):
        self._abi_dir: Path = validate_directory(abi_directory)
        self._abis: Dict[str, Any] = {}
        self._load_abis()

    def get_abi(
        self,
        name: str
    ) -> ABI:
        if not self._abis:
            print("No ABIs found")
        try: 
            return self._abis[name]
        except KeyError as e:
            raise ABIException("ABI does not exist")

    def _load_abis(self) -> None:
        for file in self._abi_dir.glob('*.json'):
            name = file.stem
            try:
                with file.open() as f:
                    self._abis[name] = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error reading from {self._abi_dir} for {file}: {e}")
        if not self._abis:
            print("No ABIs found")
