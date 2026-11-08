import os
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


project_dir = '/home/barindas/prog/VotingSimulator'
DB_FILE = f"{project_dir}/database.json"
KEY_FILE = f"{project_dir}/key.bin"


if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
else:
    db = {"registered_names": [], "used_tokens": [], "votes": []}


# Превращаем списки обратно во множества (set) для быстрой проверки
registered_names = set(db["registered_names"])
used_tokens = set(db["used_tokens"])
votes = db["votes"]


if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "rb") as f:
        key = f.read()
else:
    key = AESGCM.generate_key(bit_length=256)
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    print("Создан новый ключ шифрования и сохранен в key.bin")


aesgcm = AESGCM(key)


def save_db():
    db = {
        "registered_names": list(registered_names),
        "used_tokens": list(used_tokens),
        "votes": votes
    }
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)


def register_voter(name):
    if name in registered_names:
        print("Это имя уже регистрировалось")
        return None
    registered_names.add(name)
    token = os.urandom(16).hex()
    print(f"Ваш токен для голосования: {token}")
    save_db() # <--- Save to file
    return token


def vote(token, choice):
    if token in used_tokens:
        print("Этот токен уже использован")
        return False

    nonce = os.urandom(12)
    data = choice.encode()
    ciphertext = aesgcm.encrypt(nonce, data, None)

    votes.append({"nonce": nonce.hex(), "ciphertext": ciphertext.hex()})
    used_tokens.add(token)
    save_db() # <--- Save to file
    print("Голос принят")
    return True


def tally():
    results = {}
    for v in votes:
        try:
            nonce = bytes.fromhex(v["nonce"])
            ct = bytes.fromhex(v["ciphertext"])
            choice = aesgcm.decrypt(nonce, ct, None).decode()
            results[choice] = results.get(choice, 0) + 1
        except Exception as e:
            print(f"Ошибка при расшифровке одного из голосов: {e}")
            continue
            
    return results


while True:
    name = input("\nВаше имя: ")
    token = register_voter(name)
    
    if token:
        choice = input("За кого голосуете? ")
        vote(token, choice)
        print("Результаты:", tally())
