from web3 import Web3
from web3.contract import Contract
from web3.middleware import geth_poa_middleware
import json
import sys
from pathlib import Path

source_chain = 'avax'
destination_chain = 'bsc'
contract_info = "contract_info.json"
private_key = "ba9d6d3a37734f16b93cfe8410b60640e54048223f4baa2f9fac96096153c8ca"
account_address = '0xBF6aa3c282df65D083783CE17de5cd00e1d409D4'

def connectTo(chain):
    if chain == 'avax':
        api_url = "https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet
        w3 = Web3(Web3.HTTPProvider(api_url))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)  # 为 AVAX 添加中间件

    elif chain == 'bsc':
        api_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet
        w3 = Web3(Web3.HTTPProvider(api_url))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)  # 为 BSC 添加中间件

    else:
        raise ValueError(f"Unsupported chain: {chain}")

    return w3


def getContractInfo(chain):
    p = Path(__file__).with_name(contract_info)
    try:
        with p.open('r') as f:
            contracts = json.load(f)
    except Exception as e:
        print("Failed to read contract info")
        print("Please contact your instructor")
        print(e)
        sys.exit(1)

    return contracts[chain]

def scanBlocks(chain):
    if chain not in ['source', 'destination']:
        print(f"Invalid chain: {chain}")
        return

    try:
        w3_src = connectTo(source_chain)
        w3_dst = connectTo(destination_chain)
        source_contracts = getContractInfo("source")
        destination_contracts = getContractInfo("destination")
        source_contract_address, src_abi = source_contracts["address"], source_contracts["abi"]
        destination_contract_address, dst_abi = destination_contracts["address"], destination_contracts["abi"]

        source_contract = w3_src.eth.contract(address=source_contract_address, abi=src_abi)
        destination_contract = w3_dst.eth.contract(address=destination_contract_address, abi=dst_abi)

        src_end_block = w3_src.eth.get_block_number()
        src_start_block = src_end_block - 5
        dst_end_block = w3_dst.eth.get_block_number()
        dst_start_block = dst_end_block - 5

        arg_filter = {}

        if chain == "source":  # Source
            event_filter = source_contract.events.Deposit.create_filter(
                fromBlock=src_start_block, toBlock=src_end_block, argument_filters=arg_filter
            )
            for event in event_filter.get_all_entries():
                try:
                    txn = destination_contract.functions.wrap(
                        event.args['token'],
                        event.args['recipient'],
                        event.args['amount']
                    ).build_transaction({
                        'from': account_address,
                        'chainId': w3_dst.eth.chain_id,
                        'gas': 2000000,
                        'nonce': w3_dst.eth.get_transaction_count(account_address, 'pending')
                    })
                    signed_txn = w3_dst.eth.account.sign_transaction(txn, private_key=private_key)
                    tx_hash = w3_dst.eth.send_raw_transaction(signed_txn.rawTransaction)
                    print(f"Wrap Transaction hash: {tx_hash.hex()}")
                except Exception as e:
                    print(f"Error during wrap transaction: {e}")

        elif chain == "destination":  # Destination
            event_filter = destination_contract.events.Unwrap.create_filter(
                fromBlock=dst_start_block, toBlock=dst_end_block, argument_filters=arg_filter
            )
            for event in event_filter.get_all_entries():
                try:
                    txn = source_contract.functions.withdraw(
                        event.args['underlying_token'], event.args['to'], event.args['amount']
                    ).build_transaction({
                        'from': account_address,
                        'chainId': w3_src.eth.chain_id, 
                        'gas': 20000,
                        'nonce': w3_src.eth.get_transaction_count(account_address, 'pending')
                    })
                    signed_txn = w3_src.eth.account.sign_transaction(txn, private_key=private_key)
                    tx_hash = w3_src.eth.send_raw_transaction(signed_txn.rawTransaction)
                    print(f"Withdraw Transaction hash: {tx_hash.hex()}")
                except Exception as e:
                    print(f"Error during withdraw transaction: {e}")

    except Exception as e:
        print(f"Error in scanBlocks: {e}")

