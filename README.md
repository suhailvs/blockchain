# Crypto APP
## Migrate DB and init fixtures
```
$ ./manage.py migrate
$ ./manage.py loaddata datas
```

## Create Genesis Event
uncomment `create_genesis_event_using_utils()` in `t.py`, then run:
```
$ ./manage.py shell < t.py
```

## Sign Event Data (Client Side)
uncomment `generate_signature(xx..)` in `t.py`, then run:
```
$ python t.py
```

## Sync Blockchain

http://localhost:8000/api/sync/

## Send to server

```
curl -X POST http://127.0.0.1:8000/api/submit/ \
  -H "Content-Type: application/json" \
  -d '{
  "event_type": "update_profile_image",
  "payload": {
    "image_hash":"123458",
    "nonce": 1
  },
  "public_key": "b75ec7154c3f830b093e87c7b8145db809c63e5890b3964e83bdb5a26b5db58d",
  "signature": "94001637e208657afd6c9fdf5dda7e44ffd3f123ee5cd498a043f416a462504ab3d5cb4999284d2059871c2c8573dba5c881f5785451005eb4106a7c57691f0f",
  "previous_hash":"9f901266d041aa9689439440be314fd1d4d7eb597ddad339480bf193f437c607"
}'
```

# Misc functions

## Generate Key Pair
uncomment `generate_keys()` in `t.py`, then run:
```
$ python t.py
```

## Create Identity

login to django admin and create an Identity with: 

publickey = "b75ec7154c3f830b093e87c7b8145db809c63e5890b3964e83bdb5a26b5db58d"
nonce = 0