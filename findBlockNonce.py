#!/bin/python
import hashlib
import os
import random


def mine_block(k, prev_hash, rand_lines):
    """
        k - Number of trailing zeros in the binary representation (integer)
        prev_hash - the hash of the previous block (bytes)
        rand_lines - a set of "transactions," i.e., data to be included in this block (list of strings)

        Complete this function to find a nonce such that
        sha256(prev_hash + rand_lines + nonce)
        has k trailing zeros in its *binary* representation
    """
    if not isinstance(k, int) or k < 0:
        print("mine_block expects positive integer")
        return b'\x00'

    rand_lines_combined = ''.join(rand_lines).encode('utf-8')
    target = '0' * k

    nonce = 0
    while True:

        nonce_bytes = str(nonce).encode('utf-8')
        data = prev_hash + rand_lines_combined + nonce_bytes

        hash_result = hashlib.sha256(data).hexdigest()

        if bin(int(hash_result, 16))[-k:] == target:
            return nonce_bytes

        nonce += 1


def get_random_lines(filename, quantity):
    """
    This is a helper function to get the quantity of lines ("transactions")
    as a list from the filename given.
    Do not modify this function
    """
    lines = []
    with open(filename, 'r') as f:
        for line in f:
            lines.append(line.strip())

    random_lines = []
    for x in range(quantity):
        random_lines.append(lines[random.randint(0, quantity - 1)])
    return random_lines


if __name__ == '__main__':
    # This code will be helpful for your testing
    filename = "bitcoin_text.txt"
    num_lines = 10  # The number of "transactions" included in the block

    # The "difficulty" level. For our blocks this is the number of Least Significant Bits
    # that are 0s. For example, if diff = 5 then the last 5 bits of a valid block hash would be zeros
    # The grader will not exceed 20 bits of "difficulty" because larger values take to long
    diff = 20

    rand_lines = get_random_lines(filename, num_lines)

    prev_hash = hashlib.sha256(
        b'previous_block').digest()

    nonce = mine_block(diff, prev_hash, rand_lines)
    

    print(nonce)
