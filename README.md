# Crypto APP

## Migrate DB and init fixtures and create genesis event
```
$ ./manage.py migrate
$ ./manage.py loaddata datas
$ ./manage.py creategenesisevent
```
or run `$ bash run.sh`

## Sign Event Data (Client Side)
uncomment `generate_signature(xx..)` in `t.py`, then run:
```
$ python t.py
```

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
  "signature": "aff9a9212d12db00b51d8ba3265f0496adc079b0de7a1e9cf0b4b359dcacf718a44c8844312997fd163a2146b394a4734aaf5db59ee0ad339ca8495cf89e9f01",
  "previous_hash":"9f901266d041aa9689439440be314fd1d4d7eb597ddad339480bf193f437c607"
}'
```

# Misc functions


## Sync Blockchain

http://localhost:8000/api/sync/

## Generate Key Pair
uncomment `generate_keys()` in `t.py`, then run:
```
$ python t.py
```

## Create Identity

login to django admin and create an Identity with: 

publickey = "b75ec7154c3f830b093e87c7b8145db809c63e5890b3964e83bdb5a26b5db58d"
nonce = 0
