from client.client import Client
import time
from dependency_config import container
from utils.utils import increaseTime

alice = Client(container.get_root('alice'), container.get_token('alice'))
bob = Client(container.get_root('bob'), container.get_token('bob'))
eve = Client(container.get_root('eve'), container.get_token('eve'))
authority = Client(container.get_root('authority'),
                   container.get_token('authority'))

bobTokensStart = bob.token_contract.balance_of()

# Give Eve 5 tokens
eve.register()

# Eve deposits a coin
eve.deposit(11)

# wait to make sure that events get fired correctly
time.sleep(2)

# Eve sends her plasma coin to Bob
# TODO stop manually setting these UTXOs
utxo_id = 5
coin = eve.get_plasma_coin(utxo_id)
eve_to_bob = eve.send_transaction(
         utxo_id, coin['deposit_block'], 1, bob.token_contract.account.address)
authority.submit_block()
eve_to_bob_block = authority.get_block_number()

# Eve sends this same plasma coin to Alice
eve_to_alice = eve.send_transaction(
      utxo_id, coin['deposit_block'], 1, alice.token_contract.account.address)
authority.submit_block()

eve_to_alice_block = authority.get_block_number()

# Alice attempts to exit here double-spent coin
alice.start_exit(utxo_id, coin['deposit_block'], eve_to_alice_block)

# Bob challenges Alice's exit
bob.challenge_between(utxo_id, eve_to_bob_block)
bob.start_exit(utxo_id, coin['deposit_block'], eve_to_bob_block)

w3 = bob.root_chain.w3  # get w3 instance
increaseTime(w3, 8 * 24 * 3600)
authority.finalize_exits()

bob.withdraw(utxo_id)

bob_balance_before = w3.eth.getBalance(bob.token_contract.account.address)
bob.withdraw_bonds()
bob_balance_after = w3.eth.getBalance(bob.token_contract.account.address)
assert (bob_balance_before < bob_balance_after), \
        "END: Bob did not withdraw his bonds"

bobTokensEnd = bob.token_contract.balance_of()

print('Bob has {} tokens'.format(bobTokensEnd))
assert (bobTokensEnd == bobTokensStart + 1), \
        "END: Bob has incorrect number of tokens"

print('Plasma Cash `challengeBetween` success :)')