import time
import zmq
import msgpack
import psycopg2
import os
import threading

relogio_logico = 0
mensagens_recebidas = 0
nome_servidor = os.getenv("SERVER_NAME", "server1")
offset_relogio = 0.0
coordenador_atual = None

def get_db():
    for _ in range(30):
        try:
            return psycopg2.connect(
                host=os.getenv("DB_HOST", "db1"),
                database=os.getenv("DB_NAME", "chat_db_1"),
                user=os.getenv("DB_USER", "admin"),
                password=os.getenv("DB_PASSWORD", "password")
            )
        except:
            time.sleep(3)
    raise Exception("Erro DB")

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            login_timestamp BIGINT NOT NULL
        );
    """)
    cur.execute("CREATE TABLE IF NOT EXISTS channels (name TEXT PRIMARY KEY, created_at BIGINT);")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            channel TEXT NOT NULL,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp BIGINT NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def escutar_servidores():
    global coordenador_atual, relogio_logico
    ctx = zmq.Context()
    sub = ctx.socket(zmq.SUB)
    sub.connect("tcp://proxy:5558")
    sub.setsockopt(zmq.SUBSCRIBE, b"servers")
    while True:
        try:
            topico, raw_payload = sub.recv_multipart()
            dados = msgpack.unpackb(raw_payload, raw=False)
            if "coordenador" in dados:
                novo_lider = dados["coordenador"]
                if novo_lider != coordenador_atual:
                    print(f"[PubSub] Novo coordenador anunciado: {novo_lider}", flush=True)
                coordenador_atual = novo_lider
                if "relogio" in dados:
                    relogio_logico = max(relogio_logico, dados["relogio"])
        except:
            pass

def realizar_eleicao(ctx, ref_socket, pub):
    global coordenador_atual, relogio_logico
    try:
        relogio_logico += 1
        req_list = {
            "action": "list",
            "timestamp": int(time.time()),
            "relogio": relogio_logico,
            "payload": {}
        }
        ref_socket.send(msgpack.packb(req_list, use_bin_type=True))
        rep_list = msgpack.unpackb(ref_socket.recv(), raw=False)
        
        if "relogio" in rep_list:
            relogio_logico = max(relogio_logico, rep_list["relogio"])

        servers_list = rep_list.get("servers", [])
        if servers_list:
            servers_sorted = sorted(servers_list, key=lambda x: x.get("rank", 999))
            lider_esperado = None
            for s in servers_sorted:
                s_name = s.get("name")
                if s_name == nome_servidor:
                    lider_esperado = s_name
                    break
                try:
                    test_sock = ctx.socket(zmq.REQ)
                    test_sock.setsockopt(zmq.RCVTIMEO, 1000)
                    test_sock.connect(f"tcp://{s_name.lower()}:5555")
                    relogio_logico += 1
                    test_sock.send(msgpack.packb({
                        "action": "eleicao",
                        "timestamp": int(time.time()),
                        "relogio": relogio_logico,
                        "payload": {}
                    }, use_bin_type=True))
                    rep = msgpack.unpackb(test_sock.recv(), raw=False)
                    test_sock.close()
                    if rep.get("status") == "OK":
                        lider_esperado = s_name
                        break
                except:
                    pass

            if not lider_esperado:
                lider_esperado = nome_servidor
            
            if lider_esperado != coordenador_atual:
                print(f"[Eleição] Servidor eleito coordenador: {lider_esperado}", flush=True)

            coordenador_atual = lider_esperado
            relogio_logico += 1
            pub.send_multipart([b"servers", msgpack.packb({"coordenador": coordenador_atual, "relogio": relogio_logico}, use_bin_type=True)])
    except:
        pass

def main():
    global relogio_logico, mensagens_recebidas, offset_relogio, coordenador_atual

    init_db()
    ctx = zmq.Context()
    
    sock = ctx.socket(zmq.REP)
    sock.bind("tcp://*:5555")

    pub = ctx.socket(zmq.PUB)
    pub.connect("tcp://proxy:5557")

    ref_socket = ctx.socket(zmq.REQ)
    ref_socket.connect("tcp://referencia:5557")

    threading.Thread(target=escutar_servidores, daemon=True).start()

    relogio_logico += 1
    req_rank = {
        "action": "nome",
        "timestamp": int(time.time()),
        "relogio": relogio_logico,
        "payload": {"name": nome_servidor}
    }
    ref_socket.send(msgpack.packb(req_rank, use_bin_type=True))
    rep_rank = msgpack.unpackb(ref_socket.recv(), raw=False)
    
    if "relogio" in rep_rank:
        relogio_logico = max(relogio_logico, rep_rank["relogio"])
    
    rank = rep_rank.get("rank", 1)
    print(f"Rank {rank}", flush=True)
    
    realizar_eleicao(ctx, ref_socket, pub)
    print("Servidor online", flush=True)

    while True:
        res = {"status": "ERROR"}
        try:
            raw_msg = sock.recv()
            msg = msgpack.unpackb(raw_msg, raw=False)
            
            relogio_recebido = msg.get("relogio", 0)
            relogio_logico = max(relogio_logico, relogio_recebido)

            mensagens_recebidas += 1
            if mensagens_recebidas >= 15:
                relogio_logico += 1
                req_hb = {
                    "action": "heartbeat",
                    "timestamp": int(time.time()),
                    "relogio": relogio_logico,
                    "payload": {"name": nome_servidor}
                }
                ref_socket.send(msgpack.packb(req_hb, use_bin_type=True))
                rep_hb = msgpack.unpackb(ref_socket.recv(), raw=False)
                
                if "relogio" in rep_hb:
                    relogio_logico = max(relogio_logico, rep_hb["relogio"])

                realizar_eleicao(ctx, ref_socket, pub)

                if coordenador_atual and coordenador_atual != nome_servidor:
                    sincronizado = False
                    try:
                        coord_socket = ctx.socket(zmq.REQ)
                        coord_socket.setsockopt(zmq.RCVTIMEO, 2000)
                        coord_socket.connect(f"tcp://{coordenador_atual.lower()}:5555")
                        relogio_logico += 1
                        coord_socket.send(msgpack.packb({"action": "relogio", "timestamp": int(time.time()), "relogio": relogio_logico, "payload": {}}, use_bin_type=True))
                        rep_coord = msgpack.unpackb(coord_socket.recv(), raw=False)
                        if "hora_correta" in rep_coord:
                            server_time = rep_coord["hora_correta"] / 1000.0
                            offset_relogio = server_time - time.time()
                            sincronizado = True
                        coord_socket.close()
                    except:
                        sincronizado = False

                    if not sincronizado:
                        print(f"[Falha] Coordenador {coordenador_atual} não respondeu! Iniciando reeleição...", flush=True)
                        coordenador_atual = None
                        realizar_eleicao(ctx, ref_socket, pub)

                mensagens_recebidas = 0

            action = msg.get("action")
            payload = msg.get("payload", {})
            print(f"Acao: {action}", flush=True)

            conn = get_db()
            cur = conn.cursor()

            current_time = int(time.time() + offset_relogio)

            if action == "login":
                user = payload.get("username")
                if not user or not user.strip():
                    res = {"status": "ERROR", "message": "Username vazio"}
                else:
                    cur.execute("INSERT INTO users (username, login_timestamp) VALUES (%s, %s)", (user, current_time))
                    conn.commit()
                    res = {"status": "SUCCESS"}

            elif action == "create_channel":
                chan = payload.get("channel")
                if not chan or not chan.strip():
                    res = {"status": "ERROR", "message": "Canal inválido"}
                else:
                    cur.execute("SELECT 1 FROM channels WHERE name = %s", (chan,))
                    if cur.fetchone():
                        res = {"status": "ERROR", "message": "Canal já existe"}
                    else:
                        cur.execute("INSERT INTO channels VALUES (%s, %s)", (chan, current_time))
                        conn.commit()
                        res = {"status": "SUCCESS"}

            elif action == "list_channels":
                cur.execute("SELECT name FROM channels")
                res = {"status": "SUCCESS", "channels": [r[0] for r in cur.fetchall()]}

            elif action == "publish":
                chan = payload.get("channel")
                user = payload.get("username")
                text = payload.get("message")
                if not chan or not text:
                    res = {"status": "ERROR", "message": "Dados incompletos"}
                else:
                    cur.execute("INSERT INTO messages (channel, username, message, timestamp) VALUES (%s, %s, %s, %s)", (chan, user, text, current_time))
                    conn.commit()
                    
                    relogio_logico += 1
                    pub.send_multipart([chan.encode('utf-8'), msgpack.packb({"username": user, "message": text, "timestamp": current_time, "relogio": relogio_logico}, use_bin_type=True)])
                    res = {"status": "SUCCESS"}

            elif action == "eleicao":
                res = {"status": "OK"}

            elif action == "relogio":
                res = {"status": "SUCCESS", "hora_correta": int((time.time() + offset_relogio) * 1000)}

            cur.close()
            conn.close()

        except Exception as e:
            res = {"status": "ERROR", "message": str(e)}
            print(f"Erro: {e}", flush=True)

        relogio_logico += 1
        res["timestamp"] = int(time.time() + offset_relogio)
        res["relogio"] = relogio_logico
        sock.send(msgpack.packb(res, use_bin_type=True))

if __name__ == "__main__":
    main()