import hashlib
import json
import time
from urllib.parse import urlparse
from uuid import uuid4
from flask import Flask, jsonify, request
from flask_cors import CORS
from ecdsa import VerifyingKey, SECP256k1

class Blockchain:
    def _init_(self):
        self.chain = []
        self.current_transactions = []
        
        # Crear el bloque génesis
        self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Crea un nuevo bloque en la blockchain
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Resetear la lista de transacciones actuales
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount, signature):
        """
        Añade una nueva transacción a la lista para ser pasada al siguiente bloque
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'signature': signature
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        Crea un hash SHA-256 de un bloque
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        Algoritmo simple de Prueba de Trabajo (PoW):
        Encuentra un número p' tal que hash(pp') contenga 4 ceros iniciales.
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Valida la prueba: ¿Contiene hash(last_proof, proof) 4 ceros iniciales?
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# Instanciar el Nodo Flask
app = Flask(__name__)
CORS(app)  # Habilitar CORS para permitir conexiones desde Apps Web y Móviles

# Generar una dirección global para este nodo (ej: recompensa de minería)
node_identifier = str(uuid4()).replace('-', '')

# Instanciar la Blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    # Ejecutamos el algoritmo de prueba de trabajo para obtener la siguiente prueba
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Recompensar al minero por encontrar la prueba (sender '0' significa acuñación de nueva moneda)
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
        signature="REWARD_SIGNATURE"
    )

    # Forjar el nuevo bloque añadiéndolo a la cadena
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "¡Nuevo Bloque Forjado!",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Comprobar que los campos requeridos estén en la petición POST
    required = ['sender', 'recipient', 'amount', 'signature']
    if not all(k in values for k in required):
        return jsonify({'error': 'Faltan valores en la transacción'}), 400

    index = blockchain.new_transaction(
        values['sender'], 
        values['recipient'], 
        values['amount'], 
        values['signature']
    )

    response = {'message': f'La transacción se añadirá al Bloque {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


if __name__ == '__main__':
    import os
    # Soportar puerto dinámico para la nube (Render/Railway) o usar el 5000 local
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
