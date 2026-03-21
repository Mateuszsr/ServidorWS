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
MIN_VERSION    = "1.0.1"  # versoes abaixo disso sao bloqueadas
APP_DOWNLOAD_URL = os.environ.get("APP_DOWNLOAD_URL", "")

# ── Lista de máquinas autorizadas ──
AUTHORIZED_MACHINES = {
    "6A7CD3AEEE2E54138155E2B0": "MEU PC",
    #"11D188FF67AB7D22E2FCE705": "BIA (Miguel)",
    "C7522236B60EBA94D3A8E4D0": "Miguel",
    #"AF71B8155321808DAAD1B956": "Datenshi",
    #"030B45B72576EF9327E48E35": "Sonno",
    #"9E07DC15033572B81CC9DBE0": "NSei",
}

# ── Endereços de memória + tabela de guilds (ficam APENAS no servidor) ──
MEMORY_CONFIG = {
    "STATIC_SYSTEM_INSTANCE": 0x00D4D8AC,
    "OFF_GAMEMANAGER":        0x14,
    "OFF_TREE_HEADER":        0x3C,
    "OFF_PLAYER_OBJ":         0x40,
    "OFF_CAMERA":             0x124C,
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
    "HOOK_ADDR":              0x0063572D,
    "HOOK_SIZE":              5,
    "QUEUE_SLOTS":            512,
    "OFF_GUILD_PTR":          0x9C,
    "OFF_GUILD_STR":          0x40,
    "DAMAGE_STATIC_OFFSET":   0x00345244,
    "DAMAGE_CHAIN":           [0x00, 0x20, 0x50, 0x18, 0x50, 0x10],
    "DAMAGE_VALUE_OFF":       0x04,
    "DAMAGE_ID_OFF":          0x08,

    # ── Tabela autoritativa de guilds confirmadas ──
    # Chave  = nome exato da guild (case-sensitive, igual ao que o jogo retorna)
    # id_a   = guild_id numérico confirmado (lido via OFF_GUILD_ID → +0x08)
    # Guilds com id_a == 0 são conhecidas mas sem ID confirmado ainda.
    # Para adicionar uma nova guild: inclua aqui e faça novo deploy.
    "GUILD_IDS": {
        "BANANEIROS":       {"id_a": 17},
        "EBOYS":            {"id_a": 1004},
        "EmpeRor":          {"id_a": 176},
        "MOB":              {"id_a": 3488},
        "ANCESTRAIS":       {"id_a": 78},
        "DEATHROW":         {"id_a": 504},
        "POWERFULLL":       {"id_a": 1316},
        "ARAGORN":          {"id_a": 34},
        "FREEDOM":          {"id_a": 62},
        "Assassinos":       {"id_a": 62},
        "Tomorrowld":       {"id_a": 848},
        "RepTcheca":        {"id_a": 548},
        "Tokyo":            {"id_a": 2617},
        "Daninha":          {"id_a": 2159},
        "FIRE":             {"id_a": 239},
        "ORNOT":            {"id_a": 951},
        "RHSTUDIO":         {"id_a": 63},
        "INSS":             {"id_a": 12},
        "AoA":              {"id_a": 42},
        "LOVES":            {"id_a": 52},
        "EXALTED":          {"id_a": 222},
        "SMASH":            {"id_a": 47},
        "Space":            {"id_a": 2692},
        "Ufredews":         {"id_a": 2716},
        "EGIRLS":           {"id_a": 2},
        "TheRocks":         {"id_a": 607},
        "ARCADIA":          {"id_a": 1190},
        "DarkSword":        {"id_a": 3277},
        "Wireframe":        {"id_a": 870},
        "ANOMALIA":         {"id_a": 634},
        "HUEHUEBRBR":       {"id_a": 40},
        "SANCADORES":       {"id_a": 1154},
        "ASCENSION":        {"id_a": 523},
        "MULAMBOS":         {"id_a": 490},
        "...":              {"id_a": 176},
        "DONTCRY":          {"id_a": 0},
        "FURY":             {"id_a": 410},
        "KINGDOM":          {"id_a": 0},
        "PHOENIX":          {"id_a": 2668},
        "NOX":              {"id_a": 85},
        "SEUWDSLOT":        {"id_a": 57},
        "ALLDEATH":         {"id_a": 609},
        "ATM":              {"id_a": 42},
        "LACROU":           {"id_a": 4},
        "Raijin":           {"id_a": 49},
        "Elegidos":         {"id_a": 50},
        "NEXUS":            {"id_a": 1153},
        "SENZALA":          {"id_a": 0},
        "Origins":          {"id_a": 835},
        "VLET":             {"id_a": 251},
        "VALTRAX":          {"id_a": 26},
        "RAINBOW":          {"id_a": 2293},
        "Heineken":         {"id_a": 52},
        "LONELY":           {"id_a": 1534},
        "kOMBAT":           {"id_a": 52},
        "VIKING":           {"id_a": 0},
        "FORGLORY":         {"id_a": 1033},
        "DOMINiUM":         {"id_a": 62},
        "KADOSH":           {"id_a": 317},
        "JIUZHOU":          {"id_a": 1370},
        "NOTORIOUS":        {"id_a": 1255},
        "RANDOMS":          {"id_a": 62},
        "MalaFama":         {"id_a": 59},
        "Ritmo":            {"id_a": 1140},
        "BARBIES":          {"id_a": 214},
        "AWAKENING":        {"id_a": 4380},
        "ARMARIOmc":        {"id_a": 72},
        "STF":              {"id_a": 476},
        "MADARA":           {"id_a": 54},
        "HADES":            {"id_a": 846},
        "DELTA":            {"id_a": 43},
        "ALiga":            {"id_a": 1610},
        "kindomhear":       {"id_a": 63},
        "Defensores":       {"id_a": 0},
        "HONRA":            {"id_a": 0},
        "PLAYERS":          {"id_a": 3423},
        "Disney":           {"id_a": 2278},
        "EXCLUIDOS":        {"id_a": 353},
        "Atiesh":           {"id_a": 4410},
        "SALMOS":           {"id_a": 5170},
        "TROPASB":          {"id_a": 0},
        "governo":          {"id_a": 40},
        "DARKIN":           {"id_a": 409},
        "Gucci":            {"id_a": 1268},
        "GRAM":             {"id_a": 5192},
        "ENERGYBLUE":       {"id_a": 79},
        "MERCANTES":        {"id_a": 4497},
        "BABYMONKEY":       {"id_a": 82},
        "Pingente radiante": {"id_a": 30},
        "InfinitY":         {"id_a": 45},
        "PERIGO":           {"id_a": 470},
        "LOSTS":            {"id_a": 1041},
        "ANCESMC":          {"id_a": 61},
        "Merda":            {"id_a": 182},
        "ARCA":             {"id_a": 3470},
        "GeekPop":          {"id_a": 54},
        "NEARXBANK":        {"id_a": 71},
        "MILICIA":          {"id_a": 93},
        "TeaParty":         {"id_a": 685},
        "INBORN":           {"id_a": 4720},
        "blackcrows":       {"id_a": 0},
        "SwordForce":       {"id_a": 3487},
        "tomadachi":        {"id_a": 2582},
        "Ahjin":            {"id_a": 33},
        "Metanoia":         {"id_a": 53},
        "Resistenci":       {"id_a": 5007},
        "MedelliN":         {"id_a": 622},
        "lumen":            {"id_a": 5272},
        "RAIN":             {"id_a": 303},
        "LOVEaigrid":       {"id_a": 1432},
        "NightCrows":       {"id_a": 2260},
        "SentaVara":        {"id_a": 3555},
        "Sypher":           {"id_a": 148},
        "WHISPER":          {"id_a": 5205},
        "xSHIELDx":         {"id_a": 380},
        "HellKing":         {"id_a": 2794},
        "BloodLust":        {"id_a": 443},
        "SIMPSONS":         {"id_a": 0},
        "Akattsuki":        {"id_a": 2766},
        "STARLIGHT":        {"id_a": 463},
        "DragonBorn":       {"id_a": 2324},
        "TENEBROSOS":       {"id_a": 2236},
        "Plumas":           {"id_a": 4996},
        "IGREJA":           {"id_a": 3411},
        "BlueStain":        {"id_a": 853},
        "SWAT":             {"id_a": 4985},
        "AIZEN":            {"id_a": 5076},
        "WWE":              {"id_a": 4538},
        "Miragem":          {"id_a": 2920},
        "PARADOX":          {"id_a": 5242},
        "ChosenTeam":       {"id_a": 3882},
        "METAVERSE":        {"id_a": 3048},
        "ANTIMCS":          {"id_a": 1879},
        "xKARMAx":          {"id_a": 3252},
        "PalNaMesa":        {"id_a": 2223},
        "EndWhisper":       {"id_a": 980},
        "Ordemnegra":       {"id_a": 1970},
        "Trailblaze":       {"id_a": 3692},
        "TEQUILA":          {"id_a": 4582},
        "noisbr":           {"id_a": 5174},
        "UFREDE":           {"id_a": 136},
        "QLQUMM":           {"id_a": 3707},
        "CorvoNegro":       {"id_a": 2618},
        "Argentina":        {"id_a": 332},
        "YANOMAMI":         {"id_a": 1820},
        "BCTROSA":          {"id_a": 5282},
        "CHAMPIONS":        {"id_a": 2039},
        "BlackStar":        {"id_a": 71},
        "xGZNEWSx":         {"id_a": 3269},
        "Medieval":         {"id_a": 3006},
        "DARKOLIMPO":       {"id_a": 0},
        "Covil":            {"id_a": 1233},
        "GALAXY":           {"id_a": 1316},
        "OsMandrake":       {"id_a": 53},
        "VAGANTES":         {"id_a": 1296},
        "Ollimpo":          {"id_a": 1594},
        "MenorSP":          {"id_a": 1438},
        "xxNEXUSxx":        {"id_a": 768},
        "Eternals":         {"id_a": 779},
        "HELLHAIN":         {"id_a": 5284},
        "SUBLIME":          {"id_a": 3920},
        "LastHope":         {"id_a": 487},
        "Last":             {"id_a": 2204},
        "IRONWOLF":         {"id_a": 4325},
        "SOMBRA":           {"id_a": 1063},
        "PijaMaParT":       {"id_a": 5134},
        "AKKAD":            {"id_a": 1649},
        "Cruzados":         {"id_a": 4139},
        "Manicomio":        {"id_a": 2211},
        "LatinSoul":        {"id_a": 755},
        "SNOW":             {"id_a": 2096},
        "15103":            {"id_a": 0},
        "Evoluindo":        {"id_a": 4800},
        "MALKAVIANS":       {"id_a": 1202},
        "EXCALIBUR":        {"id_a": 3060},
        "Farmeiro":         {"id_a": 5250},
        "Creed":            {"id_a": 1765},
        "Spectators":       {"id_a": 4586},
        "Aurora":           {"id_a": 2249},
        "Derivative":       {"id_a": 3868},
        "YANG":             {"id_a": 4377},
        "PointStar":        {"id_a": 4576},
        "WonderFul":        {"id_a": 1450},
        "FENSALIR":         {"id_a": 2754},
        "TROLLS":           {"id_a": 0},
        "KoTc":             {"id_a": 1116},
        "Kawwaistas":       {"id_a": 691},
        "LHP":              {"id_a": 1060},
        "knights":          {"id_a": 1164},
        "GenX":             {"id_a": 0},
        "LAW":              {"id_a": 2961},
        "URSADA":           {"id_a": 639},
        "Pprt":             {"id_a": 3202},
        "Assasins":         {"id_a": 135},
    },
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

        def ver_tuple(v):
            try: return tuple(int(x) for x in v.split("."))
            except: return (0,)
        if ver_tuple(version) < ver_tuple(MIN_VERSION):
            return jsonify({
                "ok":  False,
                "msg": f"Versão {version} desatualizada.\nBaixe a versão mais recente pelo launcher."
            }), 403

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
