import asyncio
from typing import Any, Dict, List, Optional
from web3.types import ChecksumAddress
from pydantic import ValidationError
from web3.exceptions import ContractLogicError, ABIFunctionNotFound

from .models import UniswapData, TransactionResult, CurveData
from .constructs import BaseSwapper
from .errors import SwapException

class Uniswap(BaseSwapper):
    """
    Class for Uniswap swaps.
    Extension of BaseSwapper.

    Attributes
    ------------
    _address: :class:`str`
        Address of smart contract.
    _web3node: :class:`Web3Node`
        Instance of custom Web3Node class.
    _contract: :class:`Contract`
        Initialized contract.
    """
    def swap(
        self,
        sell_coin_address: ChecksumAddress, 
        buy_coin_address: ChecksumAddress, 
        amount: int,
        **addtional_parameters: Any
    ) -> TransactionResult:

        try:
            swap_data = UniswapData(
                tokenIn=sell_coin_address,
                tokenOut=buy_coin_address,
                recipient=self._web3node.get_address(),
                amountIn=amount,
                **addtional_parameters
            ).to_dictionary()
        except ValidationError as e:
            raise SwapException(f"Error building swap: {e}") from e
        
        transaction = self._contract.functions.exactInputSingle(
            swap_data
        ).build_transaction(
            self._web3node.build_transaction_data()
        )

        return self._web3node.send_transaction(transaction)
    
class Curve(BaseSwapper):
    """
    Class for Curve swaps.
    Extension of BaseSwapper.

    Curve swaps require a specific coin index for the specific curve pool to swap, 
    hence the helper method to check the indexes. 

    Attributes
    ------------
    _address: :class:`str`
        Address of smart contract.
    _web3node: :class:`Web3Node`
        Instance of custom Web3Node class.
    _contract: :class:`Contract`
        Initialized contract.
    """
    async def get_coin_indexes(
        self, 
        coin_addresses: List[ChecksumAddress]
    ) -> Dict[ChecksumAddress, int]:
        coin_set = set(coin_addresses)

        try: 
            num_coins = self._contract.functions.N_COINS().call()
        except (ContractLogicError, ABIFunctionNotFound) as e:
            raise SwapException(f"Error during contract call for coins: {e}") from e

        coin_tasks = [
            self._lookup_coin(i, coin_set)
            for i in range(num_coins)
        ]

        results = await asyncio.gather(*coin_tasks)
        return {k: v for result in results for k, v in result.items()}
    
    async def _lookup_coin(
        self, 
        index: int, 
        coin_set: set
    ) -> Dict[ChecksumAddress, int]:
        try:
            address = self._contract.functions.coins(index).call()
            return {address: index} if address in coin_set else {}
        except (ContractLogicError, ABIFunctionNotFound) as e:
            raise SwapException(f"Coin index lookup failed: {e}") from e
    
    def _prepare_swap(
        self, 
        sell_coin_address: ChecksumAddress, 
        buy_coin_address: ChecksumAddress, 
        amount: int, 
        min_dy: int
    ) -> CurveData:
        indexes = asyncio.run(self.get_coin_indexes([sell_coin_address, buy_coin_address]))
        if len(indexes) != 2:
            raise SwapException("Coins do not exist in pool")
        
        try:
            estimated_dy = self._contract.functions.get_dy(indexes[sell_coin_address], indexes[buy_coin_address], amount).call()
        except (ContractLogicError, ABIFunctionNotFound, ValueError) as e:
            raise SwapException(f"Error during contract call for estimated dy: {e}") from e
        
        try:
            return CurveData(
                tokenInIndex=indexes[sell_coin_address],
                tokenOutIndex=indexes[buy_coin_address],
                dy=estimated_dy,
                min_dy=min_dy,
            )
        except ValidationError as e:
            raise SwapException(f"Error building swap: {e}") from e

    def swap(
        self,
        sell_coin_address: ChecksumAddress, 
        buy_coin_address: ChecksumAddress, 
        amount: int,
        min_dy: Optional[int] = 0
    ) -> TransactionResult:
        swap_data = self._prepare_swap(sell_coin_address, buy_coin_address, amount, min_dy)

        transaction = self._contract.functions.exchange(
            *swap_data.to_args()
        ).build_transaction(
            self._web3node.build_transaction_data()
        )

        return self._web3node.send_transaction(transaction)
