from abc import ABC, abstractmethod
from web3.contract import Contract
from web3.types import ChecksumAddress

from .web3node import Web3Node, validate_web3_node
from .utils import validate_address
from .errors import SwapException
from .models import ABI, TransactionResult

class BaseContract(ABC):
    """
    Smart Contract template class for both swappers and coins.

    Attributes
    ------------
    _address: :class:`str`
        Address of smart contract.
    _web3node: :class:`Web3Node`
        Instance of custom Web3Node class.
    _contract: :class:`Contract`
        Initialized contract.
    """
    def __init__(
        self, 
        address: str, 
        abi: ABI, 
        _web3node: Web3Node
    ):
        self._address: ChecksumAddress = validate_address(address)
        self._web3node: Web3Node = validate_web3_node(_web3node)
        self._contract: Contract = self._initialize_contract(abi)

    def _initialize_contract(
        self, 
        abi: ABI
    ) -> Contract:
        try:
            return self._web3node.get_web3().eth.contract(
                address=self._address,
                abi=abi
            )
        except (ValueError, AttributeError) as e: 
            raise SwapException(f"Error while initializing swap contract: {e}")

    def get_address(
        self
    ) -> ChecksumAddress:
        return self._address

class BaseSwapper(BaseContract):
    """Template class for all swappers. 
    Extension of Base Contract

    Attributes
    ------------
    _address: :class:`str`
        Address of smart contract.
    _web3node: :class:`Web3Node`
        Instance of custom Web3Node class.
    _contract: :class:`Contract`
        Initialized contract.
    """
    @abstractmethod
    def swap(
        self, 
        *args, 
        **kwargs
    ) -> TransactionResult:
        pass
    
class BaseProgram(ABC):
    """Abstract class for all programs."""
    @abstractmethod
    def _instantiate(self) -> None:
        pass

    @abstractmethod
    def execute(self) -> None:
        pass
