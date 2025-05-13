from pydantic import BaseModel, validator
from enum import Enum
from web3.types import Nonce, ChecksumAddress
from typing import NamedTuple, Any, Dict, List, Optional, TypeAlias, Union
from hexbytes import HexBytes

ABIEntry: TypeAlias = Dict[str, Any]
ABI: TypeAlias = List[ABIEntry]

class DictionaryTranslatable(BaseModel):
    """
    Base Class for templates that need to be translated to dictionaries.
    """
    def to_dictionary(
        self
    ) -> Dict[str, Any]:
        return self.dict(exclude_none=True)

class TransactionData(DictionaryTranslatable):
    """
    Template for all transactions sent on Web3.
    """
    nonce: Nonce
    maxFeePerGas: int
    maxPriorityFeePerGas: int
    chainId: int
    value: int | None = 0
    gas: int | None = 400000
    to: ChecksumAddress | None = None
    data: str | None = None
    
class UniswapData(DictionaryTranslatable):
    """
    Template for parameters on all Uniwswap Swaps.
    """
    tokenIn: ChecksumAddress
    tokenOut: ChecksumAddress
    fee: int | None = 100
    recipient: ChecksumAddress
    amountIn: int
    amountOutMinimum: int | None = 0
    sqrtPriceLimitX96: int | None = 0

class CurveData(BaseModel):
    """
    Template for parameters on all Curve Swaps.
    """
    tokenInIndex: int
    tokenOutIndex: int
    dy: int
    min_dy: int

    def to_args(
        self
    ) -> tuple[int, int, int, int]:
        return self.tokenInIndex, self.tokenOutIndex, self.dy, self.min_dy

class TransactionStatus(Enum):
    """
    Enum to translate defeault status values to human readable statuses.
    """
    SUCCESS = 1
    FAILURE = 0
    NOT_VERIFIED = -1  
    
class GasFees(NamedTuple):
    """
    Storing gas parameters.
    """
    maxPriorityFeePerGas: int
    maxFeePerGas: int

class TransactionResult(NamedTuple):
    """
    Storing results of Transactions including status and hash for tracing.
    """
    status: TransactionStatus
    transactionHash: Union[str, HexBytes]

class ListenAndSendConfig(BaseModel):
    """
    Base attribute config for ListenAndSend Program.

    Allows for attribute validation.
    """
    amount: float
    num_blocks: int
    retries: Optional[int] = 5
    
    @validator('num_blocks')
    def validate_num_blocks(cls, value) -> int:
        if value < 0:
            raise ValueError('num_blocks cannot be negative')
        return value
    
    @validator('retries')
    def validate_retries(cls, value) -> int:
        if value < 0:
            raise ValueError('retries cannot be negative')
        return value
    
class ArbitrageConfig(BaseModel):
    """
    Base attribute config for Arbitrage Program.

    Allows for attribute validation.
    """
    amount: int
    retries: Optional[int] = 5
    
    @validator('amount')
    def validate_amount(cls, value) -> int:
        if value < 0:
            raise ValueError('amount cannot be negative')
        return value
    
    @validator('retries')
    def validate_retries(cls, value) -> int:
        if value < 0:
            raise ValueError('retries cannot be negative')
        return value
