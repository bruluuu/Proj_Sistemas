package com.chat;

import org.zeromq.ZMQ;
import org.zeromq.ZContext;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.msgpack.jackson.dataformat.MessagePackFactory;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

public class Client {
    private static final ObjectMapper mapper = new ObjectMapper(new MessagePackFactory());
    private static final String HOST = System.getenv().getOrDefault("TARGET_HOST", "server1");
    private static final String USERNAME = System.getenv().getOrDefault("CLIENT_NAME", "BotUser");

    public static void main(String[] args) {
        try { Thread.sleep(5000); } catch (InterruptedException e) {}

        try (ZContext ctx = new ZContext()) {
            ZMQ.Socket sock = ctx.createSocket(ZMQ.REQ);
            sock.connect("tcp://" + HOST + ":5555");
            System.out.println("Conectado ao servidor como " + USERNAME);

            boolean loggedIn = false;
            while (!loggedIn) {
                Map<String, Object> loginPayload = new HashMap<>();
                loginPayload.put("username", USERNAME);
                
                Map res = sendReq(sock, "login", loginPayload);
                if (res != null && "SUCCESS".equals(res.get("status"))) {
                    System.out.println("Login realizado com sucesso!");
                    loggedIn = true;
                } else {
                    System.out.println("Falha no login. Tentando novamente em 2 segundos...");
                    Thread.sleep(2000);
                }
            }

            Map<String, Object> channelPayload = new HashMap<>();
            channelPayload.put("channel", "geral");
            Map createRes = sendReq(sock, "create_channel", channelPayload);
            if (createRes != null && "SUCCESS".equals(createRes.get("status"))) {
                System.out.println("Canal 'geral' criado com sucesso.");
            } else {
                System.out.println("Canal já existe ou houve erro.");
            }

            sendReq(sock, "list_channels", new HashMap<>());

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static Map sendReq(ZMQ.Socket sock, String action, Map<String, Object> payload) throws Exception {
        Map<String, Object> req = new HashMap<>();
        req.put("action", action);
        req.put("timestamp", Instant.now().getEpochSecond());
        req.put("payload", payload);

        sock.send(mapper.writeValueAsBytes(req), 0);

        byte[] reply = sock.recv(0);
        Map res = mapper.readValue(reply, Map.class);
        
        System.out.println("Ação [" + action + "] -> Resp: " + res);
        Thread.sleep(1500);
        return res;
    }
}