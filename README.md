# Sistema de Chat Distribuído - Parte 3

Sistema de chat distribuído desenvolvido em **Python**, **Java** e **PostgreSQL**, utilizando **ZeroMQ** para comunicação de alta performance e **MessagePack** para serialização.

## Arquitetura da Parte 3

Esta terceira etapa expande a arquitetura anterior introduzindo **relógios lógicos e físicos sincronizados**, além de um serviço de referência dedicado ao gerenciamento de ranks e monitoramento de nós.

* **Serviço de Referência:** Gerencia a atribuição de ranks aos servidores, mantém a lista dinâmica de nós ativos através de heartbeats periódicos e fornece carimbos de tempo para a sincronização física do relógio.
* **Relógios Lógicos e Físicos:** Implementação de contadores lógicos causalmente ordenados em clientes e servidores (com controle de concorrência), acompanhados do cálculo de offset físico obtido nas mensagens de heartbeat.
* **Servidores e Clientes:** Processam requisições via Req-Rep, publicam e consomem mensagens via proxy Pub/Sub, disparam heartbeats a cada lote de mensagens recebidas e persistem os dados em bancos PostgreSQL independentes.
* **Padronização de Mensageria:** Uso estrito de **MessagePack** e envelopes estruturados em todas as comunicações da rede, incluindo as requisições direcionadas ao serviço de referência.

## Como Executar

Certifique-se de ter o **Docker** e o **Docker Compose** instalados.

Na raiz do projeto, execute:
```bash
docker compose up --build