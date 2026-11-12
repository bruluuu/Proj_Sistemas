# Sistema de Chat Distribuído - Parte 2

Sistema de chat distribuído desenvolvido em Python, Java e PostgreSQL, utilizando ZeroMQ para comunicação de alta performance e MessagePack para serialização.

## Arquitetura da Parte 2

Esta segunda etapa expande a arquitetura anterior introduzindo um sistema de mensageria baseado no padrão **Publisher-Subscriber (Pub/Sub)**, desacoplado do broker de Requisição-Resposta (Req-Rep).

* **Proxy Pub/Sub**: Gerencia a distribuição de tópicos (canais), operando com um socket XSUB na porta 5557 (recebendo dos servidores) e um socket PUB na porta 5558 (distribuindo para os clientes).
* **Servidores**: Continuam lidando com autenticação e requisições via Req-Rep na porta 5555, além de persistir todas as mensagens enviadas em bancos PostgreSQL independentes antes de publicá-las no proxy.
* **Clientes / Bots**: Realizam o login automático, criam/listam canais, inscrevem-se de forma aleatória em pelo menos 3 canais através do socket SUB, e publicam lotes de mensagens de forma cadenciada.

## Como Executar

Certifique-se de ter o Docker e o Docker Compose instalados.

Na raiz do projeto, execute:

```bash
docker compose up --build
```

Para iniciar novamente sem recompilar as imagens, caso não tenham ocorrido alterações no código:

```bash
docker compose up
```