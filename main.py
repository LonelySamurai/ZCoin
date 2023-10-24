import hashlib
import random
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.bindings.openssl import binding
from cryptography.hazmat.primitives.asymmetric import utils

NUM_DELEGATES = 7
THRESHOLD = 5  # Threshold for block approval
BLOCK_REWARD = 0.5  # Reward for producing a block1
TRANSACTION_FEE = 0.2  # Transaction fee for validating transactions


class Users:
    blockchain = None

    def __init__(self, ID, stakes, wallet_addr, private_key=None):
        self.ID = ID
        self.stakes = stakes
        self.wallet_addr = wallet_addr
        self.pending_transactions = []
        if private_key is None:
            self.private_key = ec.generate_private_key(ec.SECP256R1())
        else:
            self.private_key = private_key

#DIGITAL SIGNATURE
    def sign_transaction(self, transaction):
        signature = self.private_key.sign(
            transaction.encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )
        return signature

    def verify_transaction(self, transaction, signature, public_key):
        public_key.verify(
            signature,
            transaction.encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )

    def send_transaction(self, sender, recipient, amount):
        if self.blockchain:
            blockchain = self.blockchain  # Get the Blockchain instance

            if sender in blockchain.users and recipient in blockchain.users:
                sender_user = next(user for user in blockchain.users if user.ID == sender)
                recipient_user = next(user for user in blockchain.users if user.ID == recipient)

                if sender_user.stakes >= amount:
                    # Deduct the transferred stakes and transaction fee from the sender
                    sender_user.stakes -= amount + TRANSACTION_FEE
                    # Add the transferred stakes to the recipient
                    recipient_user.stakes += amount

                    # Create a transaction string including the transaction fee
                    transaction = f"{sender} -> {recipient} {amount} {TRANSACTION_FEE}"

                    # Sign and add the transaction to the pending block
                    sender_user.sign_and_add_transaction(transaction)
                    return True
                else:
                    print(f"{sender} does not have enough stakes for the transfer.")
                    return False
            else:
                print("Invalid sender or recipient.")
                return False
        else:
            print("Blockchain instance not set. Make sure to initialize Users after creating a Blockchain.")

    def sign_and_add_transaction(self, transaction):
        if self.blockchain:
            # Sign the transaction and add it to the pending block
            signature = self.sign_transaction(transaction)
            self.blockchain.transaction.append(f"{self.ID} -> {transaction} {signature}")
        else:
            print("Blockchain instance not set. Make sure to initialize Users after creating a Blockchain.")



"**************************************************************************************"

#USED FOR SELECTING DELEGATES (instead of using voting election)
class VRF:
    def __init__(self, secret_key=None):
        if secret_key is None:
            self.secret_key = ec.generate_private_key(ec.SECP256R1())
        else:
            self.secret_key = secret_key

    def generate_proof(self, message):
        message = message.encode('utf-8')
        message_hash = self.secret_key.sign(message, ec.ECDSA(hashes.SHA256()))
        return message_hash

"**************************************************************************************"


class Block:
    transactions = None
    hash = None
    prev_hash = "0" * 64

    def __init__(self, transactions, prev_hash, producer):
        self.transactions = transactions
        self.prev_hash = prev_hash
        self.producer = producer
        self.hash = self.calc_hash()

    def calc_hash(self):
        sha = hashlib.sha256()
        for tx in self.transactions:
            sha.update(tx.encode('utf-8'))
        sha.update(self.prev_hash.encode('utf-8'))
        sha.update(self.producer.ID.encode('utf-8'))  # Include producer ID
        return sha.hexdigest()

"**************************************************************************************"

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.users = []
        self.candidates = []
        self.delegates = []
        self.transaction = []
        self.vrf = VRF()
        self.current_delegate = None  # Track the current delegate producing the block
        self.pending_blocks = []  # Store pending blocks to be

        Users.blockchain = self

    def set_current_delegate(self, delegate):
        self.current_delegate = delegate

    def create_genesis_block(self):
        transactions = []
        return Block(transactions, "0", Users("Genesis", 0, "Genesis Wallet"))

    def register_user(self, ID, stakes, wallet_addr):
        user = Users(ID, stakes, wallet_addr)
        self.users.append(user)
        print(f"User {ID} registered with {stakes} stakes. [Wallet Address: {wallet_addr}]")
        self.transaction.append(f"{user.ID} -> {user.ID} {user.stakes}")
        self.add_block()

    def propose_candidate(self, user):
        if user in self.users:
            if user not in self.candidates:
                self.candidates.append(user)
                print(f"{user.ID} has proposed to become a candidate.")
            else:
                print(f"{user.ID} is already a candidate.")
        else:
            print(f"{user.ID} is not a registered user.")

    def elect_delegates(self):
        if len(self.candidates) >= NUM_DELEGATES:
            candidate_proofs = {}
            for candidate in self.candidates:
                proof = self.vrf.generate_proof(candidate.ID)
                candidate_proofs[candidate] = proof
            sorted_candidates = sorted(self.candidates, key=lambda c: candidate_proofs[c])

            self.delegates = sorted_candidates[:NUM_DELEGATES]

            self.delegates = sorted_candidates[:NUM_DELEGATES]
            print("Delegates elected:", [d.ID for d in self.delegates])
        else:
            print("Not enough candidates to elect delegates.")

    def add_block(self):
        prev_block = self.chain[-1]
        if self.current_delegate:
            new_block = Block(self.transaction, prev_block.hash, self.current_delegate)
            self.chain.append(new_block)
            self.transaction = []
        #else:
            #print("No current delegate present")

    def validate_block(self, block):
        # Check if the block producer is in the list of elected delegates
        if block.producer not in self.delegates:
            print(f"Block produced by {block.producer.ID} is not a valid delegate.")
            return False

        # Check if the block follows the rotation order
        if block.producer != self.current_delegate.ID:
            print(f"Block produced by {block.producer.ID} out of order in the rotation.")
            return False

        # Block verification by delegates
        total_transaction_fees = 0
        for transaction in block.transactions:
            sender, recipient_and_stakes, signature, transaction_fee = transaction.split(" -> ")
            recipient, stakes = recipient_and_stakes.split()
            sender_user = next(user for user in self.users if user.ID == sender)
            recipient_user = next(user for user in self.users if user.ID == recipient)
            try:
                sender_user.verify_transaction(
                    f"{sender} -> {recipient} {stakes} {transaction_fee}",
                    bytes.fromhex(signature),
                    sender_user.private_key.public_key()
                )
                total_transaction_fees += int(transaction_fee)
            except Exception as e:
                print(f"Transaction verification failed for block produced by {block.producer.ID}: {str(e)}")
                return False

        # Calculate and distribute transaction fees to the block producer
        block.producer.stakes += BLOCK_REWARD + total_transaction_fees

        return True

    def verify_block(self, block):
        # Verify digital signatures of transactions
        total_transaction_fees = 0
        for transaction in block.transactions:
            sender, recipient_and_stakes, signature, transaction_fee = transaction.split(" -> ")
            recipient, stakes = recipient_and_stakes.split()
            sender_user = next(user for user in self.users if user.ID == sender)
            recipient_user = next(user for user in self.users if user.ID == recipient)
            try:
                sender_user.verify_transaction(
                    f"{sender} -> {recipient} {stakes} {transaction_fee}",
                    bytes.fromhex(signature),
                    sender_user.private_key.public_key()
                )
                total_transaction_fees += int(transaction_fee)
            except Exception as e:
                print(f"Transaction verification failed for block produced by {block.producer.ID}: {str(e)}")
                return False

        # Calculate and distribute transaction fees to the block producer
        block.producer.stakes += BLOCK_REWARD + total_transaction_fees

        return True

    def add_block_to_chain(self, block):
        if self.validate_block(block):
            self.chain.append(block)
            self.update_stakes(block)
        else:
            print("Block validation failed. Block not added to the blockchain.")


    def update_stakes(self, block):
        for transaction in block.transactions:
            sender, recipient_and_stakes = transaction.split(" -> ")
            recipient, stakes = recipient_and_stakes.split()
            amount = int(stakes)
            sender_user = next(user for user in self.users if user.ID == sender)
            recipient_user = next(user for user in self.users if user.ID == recipient)
            sender_user.stakes -= amount
            recipient_user.stakes += amount



    def print_blockchain(self):
        for i, block in enumerate(self.chain):
            print(f"Block {i + 1}:")
            print("Previous Hash:", block.prev_hash)
            print("Hash:", block.hash)
            print("Stakes:")
            for transaction in block.transactions:
                sender, recipient_and_stakes, _ = transaction.split(" -> ")
                recipient, stakes = recipient_and_stakes.split()
                print(f"  {sender} -> {recipient} {stakes}")
            print()

    def propose_block(self, producer):
        if self.current_delegate is None:
            # Set the current delegate to a default user (Genesis) or handle it as needed
            self.set_current_delegate(Users("Genesis", 0, "Genesis Wallet"))
        prev_block = self.chain[-1]
        new_block = Block(self.transaction, prev_block.hash, producer)
        self.pending_blocks.append(new_block)
        self.transaction = []
        print(f"Block proposed by {producer.ID}.")

    def verify_pending_blocks(self):
        valid_blocks = []
        for block in self.pending_blocks:
            if self.verify_block(block):
                valid_blocks.append(block)
        return valid_blocks

    def finalize_blocks(self, valid_blocks):
        if len(valid_blocks) >= THRESHOLD:
            for block in valid_blocks:
                self.chain.append(block)
                self.update_stakes(block)
            self.pending_blocks = []
            print("Blocks added to the blockchain.")
        else:
            print("Threshold requirement not met. Blocks not added to the blockchain.")


if __name__ == "__main__":
    blockchain = Blockchain()

    while True:
        print("\nOptions:")
        print("1. Register New User")
        print("2. View List of Nodes")
        print("3. View Candidates")
        print("4. View Delegates")
        print("5. Delegates Options")
        print("6. View Blockchain")
        print("7. Exit")
        print("8. Send Transactions")

        choice = input("\nSelect an option: ")

        if choice == "1":
            ID = input("Enter user ID: ")
            stakes = int(input("Enter stakes: "))
            wallet_addr = input("Enter wallet address: ")
            blockchain.register_user(ID, stakes, wallet_addr)
        elif choice == "2":
            print("\nList of Nodes:")
            for user in blockchain.users:
                print(f"ID: {user.ID}, Stakes: {user.stakes}, Wallet Address: {user.wallet_addr}")
        elif choice == "3":
            print("\nList of Candidates:")
            for candidate in blockchain.candidates:
                print(f"ID: {candidate.ID}")
        elif choice == "4":
            print("\nCurrent Delegates:")
            for delegate in blockchain.delegates:
                print(f"ID: {delegate.ID}, Stakes: {delegate.stakes}, Wallet Address: {delegate.wallet_addr}")
        elif choice == "5":
            blockchain.elect_delegates()
            while True:
                print("\nDelegate Options:")
                print("1. Propose Block")
                print("2. Verify Pending Blocks")
                print("3. Finalize Blocks")
                print("4. View Delegates")
                print("5. Back to Main Menu")

                delegate_choice = input("Select an option: ")

                if delegate_choice == "1":
                    if blockchain.current_delegate:
                        producer = blockchain.current_delegate
                        blockchain.propose_block(producer)
                    else:
                        print("No current delegate to propose a block.")
                elif delegate_choice == "2":
                    valid_blocks = blockchain.verify_pending_blocks()
                    print(f"{len(valid_blocks)} valid block(s) found.")
                elif delegate_choice == "3":
                    valid_blocks = blockchain.verify_pending_blocks()
                    blockchain.finalize_blocks(valid_blocks)
                elif delegate_choice == "4":
                    print("\nCurrent Delegates:")
                    for delegate in blockchain.delegates:
                        print(f"ID: {delegate.ID}, Stakes: {delegate.stakes}, Wallet Address: {delegate.wallet_addr}")
                elif delegate_choice == "5":
                    break
                else:
                    print("Invalid choice. Please select a valid option.")
        elif choice == "6":
            print("\nBlockchain:")
            blockchain.print_blockchain()
        elif choice == "7":
            break

        elif choice == "8":
            sender_ID = input("Enter your user ID: ")
            recipient_ID = input("Enter the recipient's user ID: ")
            amount = float(input("Enter the amount to send: "))
            sender_user = next((user for user in blockchain.users if user.ID == sender_ID), None)
            recipient_user = next((user for user in blockchain.users if user.ID == recipient_ID), None)

            if sender_user is None:
                print(f"\nSender {sender_ID} is not a registered user.")
            elif recipient_user is None:
                print(f"\nRecipient {recipient_ID} is not a registered user.")
            elif sender_user.send_transaction(sender_ID,recipient_ID, amount):
                print(f"\nTransaction from {sender_ID} to {recipient_ID} for {amount} stakes initiated.")

        else:
            print("Invalid choice. Please select a valid option.")
