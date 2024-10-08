from web3 import Web3
import eth_account
import os
from eth_account import Account
def get_keys(challenge,keyId = 0, filename = "eth_mnemonic.txt"):
    """
    Generate a stable private key
    challenge - byte string
    keyId (integer) - which key to use
    filename - filename to read and store mnemonics

    Each mnemonic is stored on a separate line
    If fewer than (keyId+1) mnemonics have been generated, generate a new one and return that
    """

    w3 = Web3()

    msg = eth_account.messages.encode_defunct(challenge)

	#YOUR CODE HERE
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            mnemonics = f.read().splitlines()
    else:
        mnemonics = []
    while len(mnemonics) <= keyId:
        account = Account.create()
        mnemonics.append(account.key.hex())
        with open(filename, 'a') as f:
            f.write(f"{account.key.hex()}\n")
    private_key = mnemonics[keyId].strip()
    acct = Account.from_key(private_key)
    eth_addr = acct.address
    sig = w3.eth.account.sign_message(msg, private_key=private_key)


    assert eth_account.Account.recover_message(msg,signature=sig.signature.hex()) == eth_addr, f"Failed to sign message properly"

    #return sig, acct #acct contains the private key
    return sig, eth_addr

if __name__ == "__main__":
    for i in range(4):
        challenge = os.urandom(64)
        sig, addr= get_keys(challenge=challenge, keyId=i)
        print( addr )
