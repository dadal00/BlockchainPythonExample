import time
from typing import Any, Dict, Optional, Union
import requests
from web3 import Account, Web3
from web3.types import ChecksumAddress, TxParams
from web3.exceptions import TimeExhausted
from pydantic import ValidationError
from hexbytes import HexBytes

from .config import PRIVATE_KEY
from .errors import Web3ConnectionException, InvalidPrivateKeyException, TransactionException
from .models import TransactionData, GasFees, TransactionStatus, TransactionResult
from .utils import validate_address

class Web3Node:
    """
    A wrapper for the Web3 instance abstracting sending and building transactions.

    Attributes
    ------------
    _private_key: :class:`str`
        Private key for account on blockchain.
    rpc_endpoint: :class:`str`
        URL for rpc endpoint.
    retries: :class:`int`
        Optional number of retries for reconnecting to Web3.
    _web3: :class:`Web3`
        Web3 instance responsible for connecting and sending.
    _account_address: :class:`ChecksumAddress`
        Public address of account.
    """
    _private_key = PRIVATE_KEY

    def __init__(
        self, 
        rpc_endpoint: str, 
        retries: Optional[int] = 5,
    ):
        self.rpc_endpoint: str = rpc_endpoint
        self.retries: Optional[int] = retries
        
        self._web3: Optional[Web3] = None
        self._account_address: Optional[ChecksumAddress] = None

        self._initialize_web3()
        self._initialize_account_address()
    
    def get_gas_fees(
        self
    ) -> GasFees:
        latest_block = self._web3.eth.get_block('latest')
        maxPriorityFeePerGas = self._web3.eth.max_priority_fee

        base_fee = latest_block['baseFeePerGas']
        maxFeePerGas = (2 * base_fee) + maxPriorityFeePerGas

        return GasFees(maxPriorityFeePerGas, maxFeePerGas)
    
    def send_ETH(
        self,
        amount: float,
        to_address: str,
    ) -> TransactionResult:
        to_address = validate_address(to_address)
        amount_wei = self._web3.to_wei(amount, 'ether')

        tx_data = self.build_transaction_data(**{
            'to': to_address,
            'value': amount_wei,
        })

        return self.send_transaction(tx_data)
        
    def build_transaction_data(
        self, 
        **override_parameters: Any
    ) -> Dict[str, Any]:
        if 'nonce' not in override_parameters:
            override_parameters['nonce'] = self._web3.eth.get_transaction_count(self._account_address)
        
        if 'maxFeePerGas' not in override_parameters or 'maxPriorityFeePerGas' not in override_parameters:
            gas_params = self.get_gas_fees()
            
            if 'maxFeePerGas' not in override_parameters:
                override_parameters['maxFeePerGas'] = gas_params.maxFeePerGas
            
            if 'maxPriorityFeePerGas' not in override_parameters:
                override_parameters['maxPriorityFeePerGas'] = gas_params.maxPriorityFeePerGas
        if 'chainId' not in override_parameters:
            override_parameters['chainId'] = self._web3.eth.chain_id
        try:
            tx_data = TransactionData(**override_parameters).to_dictionary()
        except ValidationError as e:
            raise TransactionException(f"Error building transaction: {e}")
        
        return tx_data
        
    def verify_transaction(
        self, 
        transaction_hash: Union[str, HexBytes], 
        timeout: Optional[int] = 120
    ) -> TransactionStatus:
        try:
            receipt = self._web3.eth.wait_for_transaction_receipt(transaction_hash, timeout=timeout)
            return TransactionStatus(receipt.status)
        except (TimeExhausted, requests.exceptions, ValueError) as e:
            print("Error verifying transaction: {}", e)
            return TransactionStatus.NOT_VERIFIED
    
    def send_transaction(
        self, 
        transaction: TxParams
    ) -> TransactionResult:
        try:
            signed_transaction = self._web3.eth.account.sign_transaction(transaction, self._private_key)
        except (ValueError, TypeError) as e:
            raise TransactionException(f"Signing failed: {e}")
        
        try:
            transaction_hash = self._web3.eth.send_raw_transaction(signed_transaction.raw_transaction)
        except ValueError as e:
            raise TransactionException(f"RPC error sending tx: {e}")
        except requests.exceptions.RequestException as e:
            raise TransactionException(f"Network error: {e}")
        
        return TransactionResult(status=self.verify_transaction(transaction_hash), transactionHash=transaction_hash)

    def get_web3(self) -> Web3:
        return self._web3
    
    def get_address(self) -> ChecksumAddress:
        return self._account_address
        
    def _initialize_web3(self) -> None:

        self._web3 = Web3(Web3.HTTPProvider(self.rpc_endpoint))
        
        retried = 0
        while not self._web3.is_connected() and retried != self.retries:
            print("Web3 connection failed. Retrying..")
            time.sleep(1)
            retried += 1

            self._web3 = Web3(Web3.HTTPProvider(self.rpc_endpoint))

        if not self._web3.is_connected():
            raise Web3ConnectionException("Unable to connect to RPC endpoint")
        
    def _validate_key(self) -> Account:
        try:
            return Account.from_key(self._private_key)
        except (ValueError, TypeError) as e:
            raise InvalidPrivateKeyException(f"Environment private key is invalid: {e}")
    
    def _initialize_account_address(self) -> None:
        account = self._validate_key()
        self._account_address = account.address

def validate_web3_node(
    _web3_node: Web3Node
) -> Web3Node:
    if not isinstance(_web3_node, Web3Node):
        raise TypeError("Expected a web3_node instance")
    return _web3_node
