# Sistema de Chat Distribuído - Parte 5: Consistência e Replicação

Sistema de chat distribuído desenvolvido em **Python, Java e PostgreSQL**, utilizando **ZeroMQ** para comunicação de alta performance, **MessagePack** para serialização e uma arquitetura resiliente com balanceamento de carga, eleição de líderes, sincronização de relógios e replicação total de dados entre os nós.

---

## Arquitetura do Sistema

Esta etapa final consolida todas as camadas anteriores e introduz mecanismos robustos de consistência e tolerância a falhas:

* **Serviço de Referência:** Gerencia a atribuição dinâmica de ranks aos servidores, mantém a lista de nós ativos através de *heartbeats* periódicos e fornece carimbos de tempo para a sincronização física do relógio (Berkeley).
* **Proxy TCP Transparente (Load Balancer):** Atua na porta `5555` realizando o balanceamento de carga *round-robin* das requisições dos clientes entre os servidores ativos de forma totalmente transparente aos pacotes binários MessagePack.
* **Relógios Lógicos e Físicos:** Contadores lógicos causalmente ordenados em clientes e servidores, acompanhados do cálculo de offset físico obtido nas mensagens de controle.
* **Parte 5 - Consistência e Replicação Ativa:** Para garantir que todos os servidores possuam uma cópia completa e idêntica de todas as mensagens, canais e usuários (evitando perda de histórico caso um nó caia), foi implementado um modelo de **Replicação Ativa baseada em Mensagens (State Machine Replication via Pub/Sub Broadcast)** complementada com **Sincronização de Estado Inicial (Catch-up Sync)**:
  * **Propagação em Tempo Real:** Toda operação de escrita (`login`, `create_channel`, `publish`) processada por um servidor é imediatamente transmitida aos demais nós através de um tópico dedicado de replicação no barramento Pub/Sub (`tcp://proxy:5557`/`5558`).
  * **Sincronização no Boot:** Ao inicializar, cada servidor consulta os nós vizinhos (`get_state`) para recuperar todo o histórico acumulado caso tenha ficado offline, garantindo consistência eventual imediata.
  * **Idempotência:** As inserções nas bases de dados PostgreSQL (`db1`, `db2`, `db3`) utilizam restrições e verificações (`NOT EXISTS` / `ON CONFLICT DO NOTHING`) para evitar duplicações de dados.

---

## Como Executar

Certifique-se de ter o **Docker** e o **Docker Compose** instalados na sua máquina.

### 1. Primeira Execução (ou Reconstrução Completa)
Para limpar volumes antigos e subir todo o ambiente do zero com o build atualizado:

```bash
docker compose down --volumes --remove-orphans
docker compose up --build

## Execuções Posteriores

Caso o *build* já tenha sido realizado anteriormente e você queira apenas iniciar o sistema rapidamente sem recompilar as imagens:

```bash
docker compose up