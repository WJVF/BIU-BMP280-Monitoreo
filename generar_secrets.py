import json

with open('serviceAccountKey.json') as f:
    data = json.load(f)

print('[firebase]')
print('database_url = "https://estacion-metereologica-d7c0d-default-rtdb.firebaseio.com"')
print('nodo_raiz = "lecturas"')
print()
print('[firebase_credentials]')
for k, v in data.items():
    # El private_key necesita comillas triples para preservar los saltos de línea
    if k == 'private_key':
        print(f'{k} = """{v}"""')
    else:
        print(f'{k} = "{v}"')
