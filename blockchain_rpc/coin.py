from web3.types import ChecksumAddress

from .models import TransactionResult
from .constructs import BaseContract
from .utils import validate_address
from .errors import CoinException

class ERC20Coin(BaseContract):
    """
    ERC20 Coin or Stable Coin class.
    Extension of BaseContract.

    Attributes
    ------------
    _address: :class:`str`
        Address of smart contract.
    _web3node: :class:`Web3Node`
        Instance of custom Web3Node class.
    _contract: :class:`Contract`
        Initialized contract.
    """
    def approve(
        self,
        address: ChecksumAddress,
        amount: int
    ) -> TransactionResult:
        validate_address(address)
        if not isinstance(amount, int):
            raise CoinException("Expected int for amount")

        transaction = self._contract.functions.approve(
            address,
            amount
        ).build_transaction(
            self._web3node.build_transaction_data()
        )

        return self._web3node.send_transaction(transaction)
