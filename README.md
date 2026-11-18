Sistema de Chat Distribuído 

Sistema de chat distribuído completo desenvolvido em Python, Java e PostgreSQL, utilizando ZeroMQ para comunicação de alta performance e MessagePack para serialização.

Arquitetura Geral do Sistema

O projeto foi desenvolvido em etapas evolutivas, culminando em uma arquitetura robusta, tolerante a falhas, com sincronização de relógios e consistência total de dados:

Camada de Rede e Proxy (Broker): Um proxy TCP transparente na porta 5555 realiza o balanceamento de carga round-robin das requisições dos clientes entre os servidores ativos do cluster.

Serviço de Referência: Gerencia o registro dinâmico e os ranks dos servidores, monitora nós ativos via heartbeats e fornece o carimbo de tempo para a sincronização física.

Relógios Lógicos e Físicos: Contadores lógicos causalmente ordenados incorporados às mensagens e cálculo de offset físico baseado no relógio do coordenador atual para alinhar o tempo do cluster.

Eleição de Coordenador e Tolerância a Falhas: Algoritmo dinâmico de escolha de líder baseado em ranks, com verificação de saúde por heartbeat e detecção de falhas com timeout otimizado para evitar falsos positivos.

Consistência e Replicação Ativa (Parte 5):

Propagação em Tempo Real: Toda mutação de estado (login, create_channel, publish) processada por um servidor é replicada instantaneamente aos demais nós através de um barramento interno de Pub/Sub (replication).

Sincronização Inicial (Catch-up Sync): Ao subir ou recuperar de uma queda, cada servidor puxa o histórico completo (users, channels, messages) dos pares ativos via sockets REQ/REP (get_state), garantindo que todos possuam 100% dos dados.

Idempotência: Inserções seguras no PostgreSQL utilizando restrições e verificações (NOT EXISTS / ON CONFLICT DO NOTHING) para evitar duplicidade.

Como Executar

Certifique-se de ter o Docker e o Docker Compose instalados.

1. Primeira Execução (ou Reconstrução Completa)

Para limpar volumes antigos do banco e subir o ambiente do zero:

docker compose down --volumes --remove-orphans
docker compose up --build


Execuções Posteriores

Caso o build já tenha sido realizado anteriormente e você queira apenas iniciar o sistema rapidamente sem recompilar as imagens:

docker compose up
