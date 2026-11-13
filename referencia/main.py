import zmq
import time
import msgpack

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5557")

servidores = {}
ranks = {}
contador_rank = 1
relogio_logico = 0

print("Referencia rodando", flush=True)

while True:
    try:
        raw_msg = socket.recv()
        msg = msgpack.unpackb(raw_msg, raw=False)
        
        relogio_recebido = msg.get("relogio", 0)
        relogio_logico = max(relogio_logico, relogio_recebido)

        action = msg.get("action")
        payload = msg.get("payload", {})
        
        agora = time.time()
        para_remover = [s for s, t in servidores.items() if agora - t > 30]
        for s in para_remover:
            if s in servidores: del servidores[s]
            if s in ranks: del ranks[s]

        res = {"status": "ERROR"}

        if action == "nome":
            nome = payload.get("name")
            if nome:
                if nome not in ranks:
                    ranks[nome] = contador_rank
                    contador_rank += 1
                servidores[nome] = agora
                res = {"status": "SUCCESS", "rank": ranks[nome]}

        elif action == "list":
            lista = [{"name": n, "rank": r} for n, r in ranks.items()]
            res = {"status": "SUCCESS", "servers": lista}

        elif action == "heartbeat":
            nome = payload.get("name")
            if nome and nome in ranks:
                servidores[nome] = agora
                res = {"status": "SUCCESS", "server_time": agora}
            else:
                res = {"status": "ERROR", "message": "Desconhecido"}

        relogio_logico += 1
        res["timestamp"] = int(time.time())
        res["relogio"] = relogio_logico
        socket.send(msgpack.packb(res, use_bin_type=True))
    except Exception as e:
        print(f"Erro ref: {e}", flush=True)