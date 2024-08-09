from web3 import Web3
from web3.contract import Contract
from web3.providers.rpc import HTTPProvider
from web3.middleware import geth_poa_middleware # Necessary for POA chains
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
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet

    if chain in ['avax', 'bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def getContractInfo(chain):
    """
        Load the contract_info file into a dictionary
        This function is used by the autograder and will likely be useful to you
    """
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

def signAndSendTransaction(w3, account_address, private_key, transaction):
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return w3.eth.wait_for_transaction_receipt(tx_hash)


def registerAndCreateToken(source_w3, destination_w3, token_address):
    try:
        source_contract_info = getContractInfo('source')
        destination_contract_info = getContractInfo('destination')

        source_contract = source_w3.eth.contract(address=source_contract_info['address'], abi=source_contract_info['abi'])
        destination_contract = destination_w3.eth.contract(address=destination_contract_info['address'], abi=destination_contract_info['abi'])

        # Register token on the source chain
        tx = source_contract.functions.registerToken(token_address).buildTransaction({
            'from': account_address,
            'nonce': source_w3.eth.get_transaction_count(account_address),
            'gas': 2000000,
            'gasPrice': source_w3.eth.gas_price,
        })
        receipt = signAndSendTransaction(source_w3, account_address, private_key, tx)
        print(f"Token registered on source chain with transaction hash: {receipt.transactionHash.hex()}")

        # Create token on the destination chain
        tx = destination_contract.functions.createToken(token_address).buildTransaction({
            'from': account_address,
            'nonce': destination_w3.eth.get_transaction_count(account_address),
            'gas': 2000000,
            'gasPrice': destination_w3.eth.gas_price,
        })
        receipt = signAndSendTransaction(destination_w3, account_address, private_key, tx)
        print(f"Token created on destination chain with transaction hash: {receipt.transactionHash.hex()}")

    except Exception as e:
        print(f"Failed to register or create token: {e}")


def scanBlocks(chain):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function on the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """
    w3 = connectTo(source_chain if chain == 'source' else destination_chain)
    contract_info = getContractInfo(chain)
    contract_address = contract_info['address']
    contract_abi = contract_info['abi']
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    # Determine event type and corresponding function to call
    if chain == 'source':
        event_name = 'Deposit'
        opposite_chain = 'destination'
        opposite_function = 'wrap'
    else:
        event_name = 'Unwrap'
        opposite_chain = 'source'
        opposite_function = 'withdraw'

    # Scan the last 5 blocks for events
    latest_block = w3.eth.block_number
    for block_num in range(latest_block - 4, latest_block + 1):
        block = w3.eth.get_block(block_num, full_transactions=False)
        events = contract.events[event_name]().processReceipt(w3.eth.get_block_receipt(block.hash))
        
        for event in events:
            print(f"Event {event_name} found: {event}")
            opposite_w3 = connectTo(destination_chain if chain == 'source' else source_chain)
            opposite_contract_info = getContractInfo(opposite_chain)
            opposite_contract = opposite_w3.eth.contract(address=opposite_contract_info['address'], abi=opposite_contract_info['abi'])

            # Prepare the transaction to call the opposite function
            tx = opposite_contract.functions[opposite_function]().buildTransaction({
                'from': account_address,
                'nonce': opposite_w3.eth.get_transaction_count(account_address),
                'gas': 2000000,
                'gasPrice': w3.toWei('50', 'gwei'),
            })
            # Sign and send the transaction
            receipt = signAndSendTransaction(opposite_w3, account_address, private_key, tx)
            print(f"Transaction receipt: {receipt.transactionHash.hex()}")

# Example usage
if __name__ == "__main__":

    source_w3 = connectTo('avax')
    destination_w3 = connectTo('bsc')
    token_address = "0xc677c31AD31F73A5290f5ef067F8CEF8d301e45c"
    registerAndCreateToken(source_w3, destination_w3, token_address)

    # Scan both source and destination chains
    scanBlocks('source')
    scanBlocks('destination')
