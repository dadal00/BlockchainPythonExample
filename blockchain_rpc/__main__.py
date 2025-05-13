import argparse
import asyncio
from .core import ListenAndSend, Arbitrage

def main() -> None:
    parser = argparse.ArgumentParser(prog='Blockcahin RPC Simulation', description='Transaction Simulations for Swap and Send')
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    listen_parser = subparsers.add_parser("listenAndSend", help="Listens for num_blocks then sends eth amount")
    listen_parser.add_argument("amount", type=float, help="Amount to swap (eth)")
    listen_parser.add_argument("blocks", type=int, help="Number of blocks to wait")
    listen_parser.add_argument("--retries", type=int, required=False, default=5, help="Retries for Web3 connection and sending transaction")

    arbitrage_parser = subparsers.add_parser("arbitrage", help="Simulates Arbitrage transaction")
    arbitrage_parser.add_argument("amount", type=int, help="Amount to swap (coin 1)")
    arbitrage_parser.add_argument("--retries", type=int, required=False, default=5, help="Retries for Web3 connection and sending transaction")
    
    args = parser.parse_args()
    
    if args.command == "listenAndSend":
        program = ListenAndSend(amount=args.amount, num_blocks=args.blocks, retries=args.retries)
        program.execute()
    elif args.command == "arbitrage":
        loop = asyncio.get_event_loop()
        program = Arbitrage(amount=args.amount, retries=args.retries, loop=loop)
        loop.run_until_complete(program.execute())
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
