import json
from hashlib import sha256
from time import time
from urllib.parse import urlparse

import requests


class Blockchain:
    def __init__(self):
        self.nodes = set()
        self.chain = []
        self.current_transactions = []

        # genesis block
        self.new_block(previous_hash=1, proof=100)

    def register_node(self, address: str) -> None:
        """
        Adds a new Node to the list of Nodes
        :param address: Address of the node to be added. Eg: 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def new_block(self, proof: int, previous_hash=None) -> dict:
        """
        Creates a new Block in the Blockchain
        :param proof: The proof given by the Proof of work Algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash,
        }

        # reset current transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender: str, recipient: str, amount: int) -> int:
        """
        Creates a new Transaction to go into the next mined Block
        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this Transaction
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self) -> dict:
        """
        Last Block in the BlockChain
        :return: Last Block
        """
        return self.chain[-1]

    def proof_of_work(self, previous_proof: int) -> int:
        """
        Simple Proof of Work Algorithm:
          - Find q such that hash(pq) contains leading 4 zeroes, where p is the previous Proof and q is the new Proof
        :param previous_proof: Previous Proof
        :return: Proof
        """

        proof = 0
        while not self.valid_proof(previous_proof, proof):
            proof += 1

        return proof

    def resolve_conflicts(self) -> bool:
        """
        This is Consensus Algorithm. It resolves conflicts by replacing our chain, with the longest one in the network.
        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes

        new_chain = None

        # Look for longer chains
        max_length = len(self.chain)
        for node in neighbours:
            response = requests.get(f'http"//{node}/chain')

            if response.status_code == 200:
                json_response = response.json()

                if json_response['length'] > max_length and self.valid_chain(json_response['chain']):
                    max_length = json_response['length']
                    new_chain = json_response['chain']

        # Replace local chain if a valid longer chain is found
        if new_chain:
            self.chain = new_chain
            return True

        return False

    @staticmethod
    def hash(block: dict):
        """
        Creates a SHA-256 Hash of the Block
        :param block: Block
        :return: SHA-256 Hash of the Block
        """

        # `sort_keys` important for consistency
        block_string = json.dumps(block, sort_keys=True).encode()
        return sha256(block_string).hexdigest()

    @staticmethod
    def valid_proof(previous_proof: int, proof: int) -> bool:
        """
        Validates the Proof:
          Does hash(last_proof, proof) contain 4 leading zeroes?
        :param previous_proof: Previous Proof
        :param proof: Current Proof
        :return: True or False based on validation
        """

        guess = f'{previous_proof}{proof}'.encode()
        guess_hash = sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    @staticmethod
    def valid_chain(chain: list) -> bool:
        """
        Determines if the Blockchain is valid
        :param chain: Blockchain
        :return: Validity of the Blockchain
        """

        last_block = chain[0]
        for block in chain[1:]:
            if not Blockchain.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block

        return True
