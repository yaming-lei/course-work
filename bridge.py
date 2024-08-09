from web3 import Web3
from web3.contract import Contract
from web3.providers.rpc import HTTPProvider
from web3.middleware import geth_poa_middleware #Necessary for POA chains
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
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['avax','bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def getContractInfo(chain):
    """
        Load the contract_info file into a dictinary
        This function is used by the autograder and will likely be useful to you
    """
    p = Path(__file__).with_name(contract_info)
    try:
        with p.open('r')  as f:
            contracts = json.load(f)
    except Exception as e:
        print( "Failed to read contract info" )
        print( "Please contact your instructor" )
        print( e )
        sys.exit(1)

    return contracts[chain]



def scanBlocks(chain):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    if chain not in ['source','destination']:
        print( f"Invalid chain: {chain}" )
        return
    
        #YOUR CODE HERE
    src_web3 = connectTo(source_chain)
    dst_web3 = connectTo(destination_chain)

    src_contract_data = getContractInfo("source")
    dst_contract_data = getContractInfo("destination")

    src_contract = src_web3.eth.contract(address=src_contract_data["address"],
                                         abi=src_contract_data["abi"])
    dst_contract = dst_web3.eth.contract(address=dst_contract_data["address"],
                                         abi=dst_contract_data["abi"])

    src_latest_block = src_web3.eth.get_block_number()
    dst_latest_block = dst_web3.eth.get_block_number()

    src_block_range = {'start': src_latest_block - 5, 'end': src_latest_block}
    dst_block_range = {'start': dst_latest_block - 5, 'end': dst_latest_block}

    filter_params = {}

    if network == "source":  # Processing Source Chain Events
        deposit_events = src_contract.events.Deposit.create_filter(
            fromBlock=src_block_range['start'], toBlock=src_block_range['end'],
            argument_filters=filter_params)

        for event in deposit_events.get_all_entries():
            transaction = dst_contract.functions.wrap(
                event.args['token'], event.args['recipient'],
                event.args['amount']
            ).build_transaction({
                'from': account_address,
                'chainId': dst_web3.eth.chain_id,
                'gas': 5000000,
                'nonce': dst_web3.eth.get_transaction_count(account_address)
            })
            signed_transaction = dst_web3.eth.account.sign_transaction(
                transaction, private_key=private_key)
            dst_web3.eth.send_raw_transaction(
                signed_transaction.rawTransaction)

    elif network == "destination":  # Processing Destination Chain Events
        unwrap_events = dst_contract.events.Unwrap.create_filter(
            fromBlock=dst_block_range['start'], toBlock=dst_block_range['end'],
            argument_filters=filter_params)

        for event in unwrap_events.get_all_entries():
            transaction = src_contract.functions.withdraw(
                event.args['underlying_token'], event.args['to'],
                event.args['amount']
            ).build_transaction({
                'from': account_address,
                'chainId': src_web3.eth.chain_id,
                'gas': 500000,
                'nonce': src_web3.eth.get_transaction_count(account_address)
            })
            signed_transaction = src_web3.eth.account.sign_transaction(
                transaction, private_key=private_key)
            src_web3.eth.send_raw_transaction(
                signed_transaction.rawTransaction)
