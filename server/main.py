import time
import zmq
import msgpack
import psycopg2
import os

def get_db():
    for _ in range(10):
        try:
            return psycopg2.connect(
                host=os.getenv("DB_HOST", "db1"),
                database=os.getenv("DB_NAME", "chat_db_1"),
                user=os.getenv("DB_USER", "admin"),
                password=os.getenv("DB_PASSWORD", "password")
            )
        except:
            time.sleep(2)
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

def main():
    init_db()
    ctx = zmq.Context()
    
    sock = ctx.socket(zmq.REP)
    sock.bind("tcp://*:5555")

    pub = ctx.socket(zmq.PUB)
    pub.connect("tcp://proxy:5557")

    print("Servidor online", flush=True)

    while True:
        res = {"status": "ERROR"}
        try:
            msg = msgpack.unpackb(sock.recv(), raw=False)
            action = msg.get("action")
            payload = msg.get("payload", {})
            print(f"Acao: {action}", flush=True)

            conn = get_db()
            cur = conn.cursor()

            if action == "login":
                user = payload.get("username")
                if not user or not user.strip():
                    res = {"status": "ERROR", "message": "Username vazio"}
                else:
                    t = int(time.time())
                    cur.execute("INSERT INTO users (username, login_timestamp) VALUES (%s, %s)", (user, t))
                    conn.commit()
                    res = {"status": "SUCCESS"}

            elif action == "create_channel":
                chan = payload.get("channel")
                if not chan or not chan.strip():
                    res = {"status": "ERROR", "message": "Canal inválido"}
                else:
                    t = int(time.time())
                    cur.execute("SELECT 1 FROM channels WHERE name = %s", (chan,))
                    if cur.fetchone():
                        res = {"status": "ERROR", "message": "Canal já existe"}
                    else:
                        cur.execute("INSERT INTO channels VALUES (%s, %s)", (chan, t))
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
                    t = int(time.time())
                    cur.execute("INSERT INTO messages (channel, username, message, timestamp) VALUES (%s, %s, %s, %s)", (chan, user, text, t))
                    conn.commit()
                    
                    pub.send_multipart([chan.encode('utf-8'), msgpack.packb({"username": user, "message": text, "timestamp": t}, use_bin_type=True)])
                    res = {"status": "SUCCESS"}

            cur.close()
            conn.close()

        except Exception as e:
            res = {"status": "ERROR", "message": str(e)}
            print(f"Erro: {e}", flush=True)

        res["timestamp"] = int(time.time())
        sock.send(msgpack.packb(res, use_bin_type=True))

if __name__ == "__main__":
    main()