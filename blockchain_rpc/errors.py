class Web3ConnectionException(Exception):
    """Unable to connect to Web3"""

    pass

class InvalidAddressException(Exception):
    """Address format is invalid"""

    pass

class InvalidPrivateKeyException(Exception):
    """Private key is invalid"""

    pass

class TransactionException(Exception):
    """Error when processing the transaction"""

    pass

class SwapException(Exception):
    """Error when processing the swap"""

    pass

class ABIException(Exception):
    """Error when processing ABIs"""

    pass

class CoinException(Exception):
    """Error when processing coins"""

    pass
