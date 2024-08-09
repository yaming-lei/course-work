from web3 import Web3
from web3.contract import Contract
from web3.providers.rpc import HTTPProvider
from web3.middleware import geth_poa_middleware  # Necessary for POA chains
import json
import sys
from pathlib import Path

source_chain = 'avax'
destination_chain = 'bsc'
contract_info_file = "contract_info.json"
private_key = "b3d8146f623407e7691479caeefb6332b60665ad9fee90a8697feaac79b783b0"
account_address = '0x3b7f6e8011Bc2137ea1Aca77fAeDbe84Af46374A'
deployer_address = account_address
avax_rpc_url = "https://api.avax-test.network/ext/bc/C/rpc"  # Avalanche C-chain testnet
bsc_rpc_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet

tokens = [
    "0xc677c31AD31F73A5290f5ef067F8CEF8d301e45c",
    "0x0773b81e0524447784CcE1F3808fed6AaA156eC8"
]

avax_web3 = Web3(Web3.HTTPProvider(avax_rpc_url))
bsc_web3 = Web3(Web3.HTTPProvider(bsc_rpc_url))


# Load contract information from the JSON file
def getContractInfo():
    p = Path(__file__).with_name(contract_info_file)
    try:
        with p.open('r') as f:
            contracts = json.load(f)
    except Exception as e:
        print("Failed to read contract info")
        print("Please contact your instructor")
        print(e)
        sys.exit(1)

    return contracts


contract_info = getContractInfo()

destination_contract = bsc_web3.eth.contract(
    address=Web3.to_checksum_address(contract_info['destination']['address']),
    abi=contract_info['destination']['abi']
)

source_contract = avax_web3.eth.contract(
    address=Web3.to_checksum_address(contract_info['source']['address']),
    abi=contract_info['source']['abi']
)


def connectTo(chain):
    if chain == 'avax':
        api_url = avax_rpc_url
    elif chain == 'bsc':
        api_url = bsc_rpc_url

    if chain in ['avax', 'bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


def scanBlocks(chain):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function on the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    if chain not in ['source', 'destination']:
        print(f"Invalid chain: {chain}")
        return

    # YOUR CODE HERE
    w3_src = connectTo(source_chain)
    w3_dst = connectTo(destination_chain)
    source_contracts = contract_info['source']
    destination_contracts = contract_info['destination']

    src_end_block = w3_src.eth.get_block_number()
    src_start_block = src_end_block - 5
    dst_end_block = w3_dst.eth.get_block_number()
    dst_start_block = dst_end_block - 5

    arg_filter = {}
    if chain == "source":  # Source

        event_filter = source_contract.events.Deposit.create_filter(
            fromBlock=src_start_block, toBlock=src_end_block,
            argument_filters=arg_filter)
        for event in event_filter.get_all_entries():
            txn = destination_contract.functions.wrap(event.args['token'],
                                                      event.args['recipient'],
                                                      event.args[
                                                          'amount']).build_transaction(
                {
                    'from': account_address,
                    'chainId': w3_dst.eth.chain_id,
                    'gas': 5000000,
                    'nonce': w3_dst.eth.get_transaction_count(account_address)
                })
            signed_txn = w3_dst.eth.account.sign_transaction(txn,
                                                             private_key=private_key)
            w3_dst.eth.send_raw_transaction(signed_txn.rawTransaction)

    elif chain == "destination":  # Destination

        event_filter = destination_contract.events.Unwrap.create_filter(
            fromBlock=dst_start_block, toBlock=dst_end_block,
            argument_filters=arg_filter)
        for event in event_filter.get_all_entries():
            txn = source_contract.functions.withdraw(
                event.args['underlying_token'], event.args['to'],
                event.args['amount']).build_transaction({
                'from': account_address,
                'chainId': w3_src.eth.chain_id,
                'gas': 500000,
                'nonce': w3_src.eth.get_transaction_count(account_address)
            })
            signed_txn = w3_src.eth.account.sign_transaction(txn,
                                                             private_key=private_key)
            w3_src.eth.send_raw_transaction(signed_txn.rawTransaction)


# Register tokens on the Source contract
for token in tokens:
    nonce = avax_web3.eth.get_transaction_count(deployer_address, 'pending')
    transaction = source_contract.functions.registerToken(
        Web3.to_checksum_address(token)
    ).build_transaction({
        'from': deployer_address,
        'nonce': nonce,
        'gas': 500000,
        'gasPrice': avax_web3.to_wei('50', 'gwei')
    })

    signed_txn = avax_web3.eth.account.sign_transaction(transaction,
                                                        private_key=private_key)
    tx_hash = avax_web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"registerToken Transaction hash: {tx_hash.hex()}")

    avax_web3.eth.wait_for_transaction_receipt(tx_hash)

# Create tokens on the Destination contract
for token in tokens:
    nonce = bsc_web3.eth.get_transaction_count(deployer_address, 'pending')
    transaction = destination_contract.functions.createToken(
        Web3.to_checksum_address(token),
        "Wrapped Token",  # You can customize the token name
        "WTKN"  # You can customize the token symbol
    ).build_transaction({
        'from': deployer_address,
        'nonce': nonce,
        'gas': 500000,
        'gasPrice': bsc_web3.to_wei('50', 'gwei')
    })

    signed_txn = bsc_web3.eth.account.sign_transaction(transaction,
                                                       private_key=private_key)
    tx_hash = bsc_web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"createToken Transaction hash: {tx_hash.hex()}")

    bsc_web3.eth.wait_for_transaction_receipt(tx_hash)
