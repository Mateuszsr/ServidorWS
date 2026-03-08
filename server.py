"""
Warspear Tracker - Servidor de Licenças
Deploy no Render.com como Web Service (Python)
"""

from flask import Flask, request, jsonify
import hashlib
import hmac
import json
import os
import base64

app = Flask(__name__)

# ── Chave secreta do servidor (mude para algo aleatório seu) ──
# No Render, defina como variável de ambiente: SERVER_SECRET
SERVER_SECRET = os.environ.get("SERVER_SECRET", "xK9#mP2$wQ7!nL4")

# ── Versão atual do app (atualize aqui a cada nova versão) ──
LATEST_VERSION = "1.0.1"
# URL publica do arquivo .py mais recente (ex: GitHub raw, Google Drive, etc)
APP_DOWNLOAD_URL = os.environ.get("APP_DOWNLOAD_URL", "https://github.com/Mateuszsr/ServidorWS/raw/main/ArinarTracker.exe")

# ── Lista de máquinas autorizadas ──
# Adicione o machine_id de cada usuário aqui
# Para adicionar: rode o app, copie o ID que aparece na tela, cole aqui
AUTHORIZED_MACHINES = {
    "6A7CD3AEEE2E54138155E2B0": "MEU PC",
    "11D188FF67AB7D22E2FCE705": "BIA (Miguel)",
    "741884D1A444FDD018B48AA5": "Usopp",
    "C7522236B60EBA94D3A8E4D0": "Miguel",
    "AF71B8155321808DAAD1B956": "Datenshi",
    "030B45B72576EF9327E48E35": "Sonno",
    # "MACHINE_ID_AQUI": "Nome do usuário",
    # Exemplo:
    # "A1B2C3D4E5F6G7H8I9J0K1L2": "Meu PC",
}

# ── Endereços de memória (ficam APENAS no servidor) ──
MEMORY_CONFIG = {
    "STATIC_SYSTEM_INSTANCE": 0x00D3D82C,
    "OFF_GAMEMANAGER":        0x14,
    "OFF_TREE_HEADER":        0x3C,
    "OFF_PLAYER_OBJ":         0x40,
    "OFF_CAMERA":             1145 * 4,
    "OFF_NODE_LEFT":          0x04,
    "OFF_NODE_RIGHT":         0x08,
    "OFF_NODE_ID":            0x10,
    "OFF_NODE_OBJECT":        0x14,
    "OFF_WORLD_X":            0x10,
    "OFF_WORLD_Y":            0x14,
    "OFF_NAME":               0x64,
    "OFF_CUR_HP":             268,
    "OFF_MAX_HP":             272,
    "OFF_CUR_MANA":           276,
    "OFF_MAX_MANA":           280,
    "OFF_CLASS_ID":           0x3ED,
    "OFF_CAM_ZOOM":           0x30,
    "OFF_CAM_X":              0x64,
    "OFF_CAM_Y":              0x68,
    "OFF_CAM_PREV_X":         0x6C,
    "OFF_CAM_PREV_Y":         0x70,
    "OFF_VP_LEFT":            0x76,
    "OFF_VP_TOP":             0x78,
    "OFF_VP_RIGHT":           0x7A,
    "OFF_VP_BOTTOM":          0x7C,
    "HOOK_ADDR":              0x0062EC6A,
    "HOOK_SIZE":              7,
    "QUEUE_SLOTS":            512,
    "DAMAGE_STATIC_OFFSET":   0x00345244,
    "DAMAGE_VALUE_OFF":       0x04,
    "DAMAGE_ID_OFF":          0x08,
}

def encrypt_config(data: dict, machine_id: str) -> str:
    """Criptografa o config usando XOR com chave derivada de SERVER_SECRET + machine_id."""
    payload = json.dumps(data).encode()
    key = hmac.new(
        SERVER_SECRET.encode(),
        machine_id.upper().encode(),
        hashlib.sha256
    ).digest()
    encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(payload))
    return base64.b64encode(encrypted).decode()

def sign_response(data: str, machine_id: str) -> str:
    """Assina a resposta para o cliente verificar autenticidade."""
    msg = f"{machine_id}:{data}".encode()
    return hmac.new(SERVER_SECRET.encode(), msg, hashlib.sha256).hexdigest()[:16]


@app.route("/auth", methods=["POST"])
def auth():
    try:
        body       = request.get_json(force=True)
        machine_id = body.get("machine_id", "").strip().upper()
        version    = body.get("version", "0")

        if not machine_id:
            return jsonify({"ok": False, "msg": "ID inválido"}), 400

        if machine_id not in AUTHORIZED_MACHINES:
            return jsonify({
                "ok":  False,
                "msg": f"Máquina não autorizada.\nSeu ID: {machine_id}"
            }), 403

        # Encripta config para aquela máquina específica
        encrypted = encrypt_config(MEMORY_CONFIG, machine_id)
        sig       = sign_response(encrypted, machine_id)

        return jsonify({
            "ok":             True,
            "user":           AUTHORIZED_MACHINES[machine_id],
            "payload":        encrypted,
            "sig":            sig,
            "latest_version": LATEST_VERSION,
            "update_url":     APP_DOWNLOAD_URL,
        })

    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "online"})


@app.route("/version", methods=["GET"])
def version():
    return jsonify({
        "latest_version": LATEST_VERSION,
        "update_url":     APP_DOWNLOAD_URL,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
