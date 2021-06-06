"""
Flask app for the Lame Blockchain
"""
from os import environ
from uuid import uuid4

from flask import Flask, jsonify, request

from blockchain import Blockchain

app = Flask('lame-blockchain')

# Globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    # Run Proof of Work algorithm
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Reward for mining
    blockchain.new_transaction(sender='0', recipient=node_identifier, amount=1)

    # Create the new Block in the BlockChain
    last_hash = blockchain.hash(last_block)
    new_block = blockchain.new_block(proof, last_hash)

    response = {
        'message': 'New Block forged',
        'block': new_block
    }

    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check for required fields in POST data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        response = {
            'error': 'Missing values'
        }
        return jsonify(response), 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    try:
        nodes = values['nodes']
    except KeyError:
        response = {
            'error': 'Missing list of nodes'
        }
        return jsonify(response), 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }

    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    response = {
        'message': 'Our chain was replaced',
        'chain': blockchain.chain,
    } if replaced else {
        'message': 'Our chain is authoritative',
        'chain': blockchain.chain
    }

    return jsonify(response), 200


if __name__ == '__main__':
    try:
        PORT = environ['PORT']
        PORT = int(PORT)
    except (KeyError, ValueError):
        PORT = 5000
    app.run(host='0.0.0.0', port=PORT)
