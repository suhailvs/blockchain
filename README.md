# Crypto APP

## Migrate DB and init fixtures and create genesis transaction
```
$ ./manage.py migrate
$ ./manage.py loaddata datas
$ ./manage.py creategenesisevent
```
or run `$ bash run.sh`

## Sign Transaction Data (Client Side)
uncomment `generate_signature(xx..)` in `t.py`, then run:
```
$ python t.py
```

## Send to server
Transaction
```
curl -X POST http://127.0.0.1:8000/api/submit/ \
  -H "Content-Type: application/json" \
  -d '{
  "tx_type": 2,
  "public_key": "b75ec7154c3f830b093e87c7b8145db809c63e5890b3964e83bdb5a26b5db58d",
  "receiver_pubkey": "9692355f209282a3d5e34bd34207df8db87c5d96f4f58a44883bbd0d9d9222fa",
  "amount": 10,
  "height":1,
  "signature": "ed718608538c05b4b76476e0cac9ec776dcab464e39e0be98d1ad6be766341c5943cd7da88ab03ea8fbe4c11f62a17211b7992009eb9c461e6fa44e13af7340b",
  "previous_hash": "471859163112f969898719911505099ff8a1aa3e9563d584f2c552384895a2f7"
}'
```

Create User:
```
curl -X POST http://127.0.0.1:8000/api/submit/ \
  -H "Content-Type: application/json" \
  -d '{
  "tx_type": 1,
  "public_key": "b75ec7154c3f830b093e87c7b8145db809c63e5890b3964e83bdb5a26b5db58d",
  "receiver_pubkey": "","amount": 0, "height":2,
  "signature": "96b33e3158fc23af4edc7404e658da38854d0e6edf96ff5cc0104dbb2fb17a871320754eeb55762defc0382097be7d869d082a9aba879a668e232a4fb245dc0a",
  "previous_hash": "03231c4d913cd71c59b47db6f5844f65a13ed8816a4b66679faafd60a1317e37"
}'
```
# Misc functions


## Sync Blockchain

`$ ./manage.py syncblockchain`

## Generate Key Pair
uncomment `ed25519_key_from_mnemonic()` in `t.py`, then run:
```
$ python t.py
```

# TODO

+ check if a event is submited to a node which's publickey in not added to nodes
+ (i didn't thinked about it much just a quick thougt)what if transaction validation while syncing peers, the balance will not match
