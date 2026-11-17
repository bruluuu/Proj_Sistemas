package com.chat;

import org.zeromq.ZMQ;
import org.zeromq.ZContext;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.msgpack.jackson.dataformat.MessagePackFactory;

import java.time.Instant;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.atomic.AtomicInteger;

public class Client {
    private static final ObjectMapper mapper = new ObjectMapper(new MessagePackFactory());
    private static final String HOST = System.getenv().getOrDefault("SERVER_HOST", "proxy");
    private static final String USERNAME = System.getenv().getOrDefault("CLIENT_NAME", "BotUser");
    
    private static final AtomicInteger relogioLogico = new AtomicInteger(0);

    private static ZMQ.Socket createReqSocket(ZContext ctx) {
        ZMQ.Socket sock = ctx.createSocket(ZMQ.REQ);
        sock.setLinger(0);
        sock.setReceiveTimeOut(3000);
        sock.connect("tcp://" + HOST + ":5555");
        return sock;
    }

    public static void main(String[] args) {
        try { Thread.sleep(5000); } catch (InterruptedException e) {}

        try (ZContext ctx = new ZContext()) {
            ZMQ.Socket reqSock = createReqSocket(ctx);
            System.out.println("Conectado como " + USERNAME);

            boolean loggedIn = false;
            while (!loggedIn) {
                try {
                    Map<String, Object> payload = new HashMap<>();
                    payload.put("username", USERNAME);
                    Map res = sendReq(reqSock, "login", payload);
                    if (res != null && "SUCCESS".equals(res.get("status"))) {
                        loggedIn = true;
                    } else {
                        reqSock.close();
                        reqSock = createReqSocket(ctx);
                        Thread.sleep(2000);
                    }
                } catch (Exception e) {
                    reqSock.close();
                    reqSock = createReqSocket(ctx);
                    Thread.sleep(2000);
                }
            }

            Map listRes = null;
            while (listRes == null) {
                try {
                    listRes = sendReq(reqSock, "list_channels", new HashMap<>());
                    if (listRes == null) {
                        reqSock.close();
                        reqSock = createReqSocket(ctx);
                        Thread.sleep(1000);
                    }
                } catch (Exception e) {
                    reqSock.close();
                    reqSock = createReqSocket(ctx);
                    Thread.sleep(1000);
                }
            }
            List<String> channels = (List<String>) listRes.get("channels");

            if (channels == null || channels.size() < 5) {
                try {
                    Map<String, Object> cPayload = new HashMap<>();
                    cPayload.put("channel", "canal_" + new Random().nextInt(1000));
                    Map cRes = sendReq(reqSock, "create_channel", cPayload);
                    if (cRes == null) {
                        reqSock.close();
                        reqSock = createReqSocket(ctx);
                    }
                    listRes = sendReq(reqSock, "list_channels", new HashMap<>());
                    if (listRes != null) {
                        channels = (List<String>) listRes.get("channels");
                    }
                } catch (Exception e) {
                    reqSock.close();
                    reqSock = createReqSocket(ctx);
                }
            }

            ZMQ.Socket subSock = ctx.createSocket(ZMQ.SUB);
            subSock.connect("tcp://proxy:5558");
            
            if (channels != null) {
                Collections.shuffle(channels);
            }

            int subscribedCount = 0;
            if (channels != null) {
                for (String ch : channels) {
                    if (subscribedCount < 3) {
                        subSock.subscribe(ch.getBytes(ZMQ.CHARSET));
                        subscribedCount++;
                    }
                }
            }

            Thread listenerThread = new Thread(() -> {
                while (!Thread.currentThread().isInterrupted()) {
                    try {
                        byte[] channelBytes = subSock.recv(0);
                        byte[] payloadBytes = subSock.recv(0);
                        if (channelBytes != null && payloadBytes != null) {
                            String channelName = new String(channelBytes, ZMQ.CHARSET);
                            Map msgData = mapper.readValue(payloadBytes, Map.class);
                            
                            if (msgData.containsKey("relogio")) {
                                int relogioRecebido = ((Number) msgData.get("relogio")).intValue();
                                int current, updated;
                                do {
                                    current = relogioLogico.get();
                                    updated = Math.max(current, relogioRecebido);
                                } while (!relogioLogico.compareAndSet(current, updated));
                            }

                            long recvTime = Instant.now().getEpochSecond();
                            System.out.println("Recebido [" + channelName + "] de " + msgData.get("username") + ": " + msgData.get("message") + " (Envio: " + msgData.get("timestamp") + ", Recv: " + recvTime + ", Relogio: " + relogioLogico.get() + ")");
                        }
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }
            });
            listenerThread.setDaemon(true);
            listenerThread.start();

            Random rand = new Random();
            while (true) {
                if (channels != null && !channels.isEmpty()) {
                    String targetChan = channels.get(rand.nextInt(channels.size()));
                    for (int i = 0; i < 10; i++) {
                        try {
                            Map<String, Object> pubPayload = new HashMap<>();
                            pubPayload.put("channel", targetChan);
                            pubPayload.put("username", USERNAME);
                            pubPayload.put("message", "Msg teste " + i);
                            Map res = sendReq(reqSock, "publish", pubPayload);
                            if (res == null) {
                                reqSock.close();
                                reqSock = createReqSocket(ctx);
                            }
                        } catch (Exception e) {
                            reqSock.close();
                            reqSock = createReqSocket(ctx);
                            Thread.sleep(2000);
                        }
                        Thread.sleep(1000);
                    }
                }
                Thread.sleep(5000);
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static Map sendReq(ZMQ.Socket sock, String action, Map<String, Object> payload) throws Exception {
        int currentClock = relogioLogico.incrementAndGet();

        Map<String, Object> req = new HashMap<>();
        req.put("action", action);
        req.put("timestamp", Instant.now().getEpochSecond());
        req.put("relogio", currentClock);
        req.put("payload", payload);

        sock.send(mapper.writeValueAsBytes(req), 0);
        byte[] reply = sock.recv(0);
        
        if (reply == null) {
            return null;
        }

        Map res = mapper.readValue(reply, Map.class);

        if (res.containsKey("relogio")) {
            int relogioRecebido = ((Number) res.get("relogio")).intValue();
            int current, updated;
            do {
                current = relogioLogico.get();
                updated = Math.max(current, relogioRecebido);
            } while (!relogioLogico.compareAndSet(current, updated));
        }

        return res;
    }
}