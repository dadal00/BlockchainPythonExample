import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
from typing import Optional
from web3.types import Address, ChecksumAddress
from web3.exceptions import TimeExhausted
import requests

from .models import (
    TransactionStatus, 
    ListenAndSendConfig, 
    ArbitrageConfig
)
from .constructs import BaseProgram, BaseSwapper
from .config import (
    TESTNET_ENDPOINT, 
    TO_ADDRESS, 
    ENDPOINT_1, 
    SWAP_ADDRESS_1, 
    COIN_1_ADDRESS_1, 
    COIN_2_ADDRESS_1,
    ENDPOINT_2,
    SWAP_ADDRESS_2,
    COIN_1_ADDRESS_2,
    COIN_2_ADDRESS_2
)
from .web3node import Web3Node
from .utils import validate_address
from .swap import Uniswap, Curve
from .abi_loader import ABILoader
from .coin import ERC20Coin

class ListenAndSend(BaseProgram):
    """
    Program for ListenAndSend.
    Extension of BaseProgram.

    Uses ListenAndSendConfig model to validate attributes.
    Ties together multiple classes to listen for new blocks and send ETH.

    Attributes
    ------------
    amount: :class:`float`
        Amount of ETH to send.
    num_blocks: :class:`int`
        Number of blocks to wait for until sending.
    retries: :class:`int`
        Optional int representing number of retries for reconnecting to Web3
        and resending ETH transaction.
    to_address: :class:`ChecksumAddress`
        Address of account to send ETH to.
    _web3node: :class:`Web3Node`
        Instance of custom Web3Node class responsible for sending and 
        building transactions.
    """
    def __init__(
        self, 
        amount: float, 
        num_blocks: int, 
        retries: Optional[int] = 5
    ):  
        config = ListenAndSendConfig(
            amount=amount,
            num_blocks=num_blocks,
            retries=retries
        )
        self.amount: float = config.amount
        self.num_blocks: int = config.num_blocks
        self.retries: Optional[int] = config.retries
        
        self.to_address: ChecksumAddress = validate_address(TO_ADDRESS)
        self._web3node: Optional[Web3Node] = None

        self._instantiate()

    def _instantiate(self) -> None:
        print("Connecting to RPC endpoint...")
        self._web3node = Web3Node(TESTNET_ENDPOINT, self.retries)
        print("Connected")

    def execute(self) -> None:
        print("Starting execution...")

        local_web3 = self._web3node.get_web3()
        current_number = local_web3.eth.get_block("latest").number
        block_count = 0
        print(f"Block number: {current_number}")

        try:
            while(True):
                try:
                    latest_number = local_web3.eth.get_block("latest").number
                    if latest_number != current_number:
                        current_number = latest_number
                        print(f"Block number: {current_number}")
                        block_count = (block_count + 1) % self.num_blocks

                        if block_count == 0:
                            print("Sending ETH...")
                            result = self._web3node.send_ETH(self.amount, self.to_address)
                            retried = 0
                            
                            while result.status != TransactionStatus.SUCCESS and retried != self.retries:
                                print("Transaction Unsucessful")
                                print("Retrying...")
                                retried += 1
                                result = self._web3node.send_ETH(self.amount, self.to_address)

                            if result.status == TransactionStatus.SUCCESS:
                                print("Transaction Succeeded")
                            elif result.status == TransactionStatus.FAILURE:
                                print("Transaction Processed but Failed")
                            else:
                                print("Transaction Not Processed")
                except (requests.exceptions.HTTPError, TimeExhausted) as e:
                    print(f"Request Error: {e}")
                    print("Retrying...")
                    time.sleep(3)
        except KeyboardInterrupt:
            print("\nProgram interrupted. Exiting gracefully...")
                        
class Arbitrage(BaseProgram):
    """
    Program for Arbitrage.
    Extension of BaseProgram.

    Ties together multiple classes to perform coin swaps mimicing an 
    Arbitrage scenario.

    Attributes
    ------------
    amount: :class:`int`
        Amount of Coin to send.
    loop: :class:`asyncio.AbstractEventLoop`
        Execution loop to enable concurrent execution.
    retries: :class:`int`
        Optional int representing number of retries for reconnecting 
        to Web3, resending failed approvals, retrying failed swaps.
    _web3node_1: :class:`Web3Node`
        Initialized instance of custom Web3Node for the first endpoint
        of the arbitrage. 
    _web3node_1: :class:`Web3Node`
        Initialized instance of custom Web3Node for the second 
        endpoint of the arbitrage. 
    _swapper_1: :class:`BaseSwapper`
        Initialized instance of a BaseSwapper class pertaining to
        first endpoint of the arbitrage.
    _swapper_2: :class:`BaseSwapper`
        Initialized instance of a BaseSwapper class pertaining to
        second endpoint of the arbitrage.
    _coin1_1: :class:`ERC20Coin`
        Initialized instance of a ERC20Coin class pertaining to
        first endpoint of the arbitrage. The coin we swap in.
    _coin2_2: :class:`ERC20Coin`
        Initialized instance of a ERC20Coin class pertaining to
        second endpoint of the arbitrage. The coin we receive.
    """
    def __init__(
        self, 
        amount: int, 
        loop: asyncio.AbstractEventLoop,
        retries: Optional[int] = 5
    ):  
        config = ArbitrageConfig(
            amount=amount,
            retries=retries
        )
        self.amount: float = config.amount
        self.retries: Optional[int] = config.retries
        self.loop: asyncio.AbstractEventLoop = loop

        self._web3node_1: Optional[Web3Node] = None
        self._web3node_2: Optional[Web3Node] = None

        self._swapper_1: Optional[BaseSwapper] = None
        self._swapper_2: Optional[BaseSwapper] = None

        self._coin1_1: Optional[ERC20Coin] = None
        self._coin2_2: Optional[ERC20Coin] = None

        self._instantiate()
    
    def _instantiate(self) -> None:
        print("Initializing Arbitrage...")
        
        abi_loader = ABILoader()

        self._web3node_1 = Web3Node(ENDPOINT_1, self.retries)
        self._web3node_2 = Web3Node(ENDPOINT_2, self.retries)

        self._swapper_1 = Uniswap(
            SWAP_ADDRESS_1, 
            abi_loader.get_abi("swap_uniswap"),
            self._web3node_1
        )
        self._swapper_2 = Curve(
            SWAP_ADDRESS_2, 
            abi_loader.get_abi("swap_curve"),
            self._web3node_2
        )

        self._coin1_1 = ERC20Coin(
            COIN_1_ADDRESS_1,
            abi_loader.get_abi("coin_erc20"),
            self._web3node_1
        )
        self._coin2_2 = ERC20Coin(
            COIN_2_ADDRESS_2,
            abi_loader.get_abi("coin_erc20"),
            self._web3node_2
        )

        print("Initialized.")

    def _swap(self, sell_coin: ERC20Coin, swapper: BaseSwapper, buy_coin_address: Address) -> None:
        result = sell_coin.approve(swapper.get_address(), self.amount)
        retried = 0
                
        while result.status != TransactionStatus.SUCCESS and retried != self.retries:
            print("Approval Unsucessful")
            print("Retrying...")
            retried += 1
            result = sell_coin.approve(swapper.get_address(), self.amount)

        if result.status == TransactionStatus.SUCCESS:
            print("Approval Succeeded")
        elif result.status == TransactionStatus.FAILURE:
            print("Approval Processed but Failed")
            return
        else:
            print("Approval Not Processed")
            return
        

        result = swapper.swap(
            sell_coin.get_address(), 
            buy_coin_address, 
            self.amount
        )
        retried = 0
                
        while result.status != TransactionStatus.SUCCESS and retried != self.retries:
            print("Swap Unsucessful")
            print("Retrying...")
            retried += 1
            result = self._swapper_1.swap(
                sell_coin.get_address(), 
                buy_coin_address, 
                self.amount
            )

        if result.status == TransactionStatus.SUCCESS:
            print("Swap Succeeded")
        elif result.status == TransactionStatus.FAILURE:
            print("Swap Processed but Failed")
            return
        else:
            print("Swap Not Processed")
            return

    async def execute(self) -> None:
        print("Starting execution...")

        with ThreadPoolExecutor(max_workers=5) as executor:
            swap_1_coroutine = self.loop.run_in_executor(
                executor,
                self._swap,
                self._coin1_1,
                self._swapper_1,
                COIN_2_ADDRESS_1,
            )
            swap_2_coroutine = self.loop.run_in_executor(
                executor,
                self._swap,
                self._coin2_2,
                self._swapper_2,
                COIN_1_ADDRESS_2,
            )

            await asyncio.gather(swap_1_coroutine, swap_2_coroutine)
