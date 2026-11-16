Sistema de Chat Distribuído - Parte 4
Sistema de chat distribuído desenvolvido em Python, Java e PostgreSQL, utilizando ZeroMQ para comunicação de alta performance e MessagePack para serialização.

Arquitetura da Parte 4
Esta quarta etapa expande a arquitetura anterior introduzindo um cluster resiliente de três nós com instâncias isoladas de bancos de dados, padronização completa de nomenclatura e aprimoramento dos mecanismos de eleição e reeleição automática de coordenadores.

Cluster de Três Nós: Expansão da infraestrutura com três servidores (server1, server2, server3) conectados diretamente a seus respectivos bancos PostgreSQL (db1, db2, db3) para total isolamento e independência de dados.

Eleição e Reeleição Dinâmica: Mecanismo refinado de eleição de liderança coordenado pelo serviço de referência, com suporte a detecção de falhas e reeleição automática em tempo de execução quando o líder ativo é interrompido.

Rede e Resolução de Nomes: Configuração avançada de rede Docker bridge (chat-net) e padronização estrita de nomes de serviços, eliminando erros de resolução de DNS entre clientes, servidores e proxy.

Comunicação e Persistência: Troca de mensagens estruturada via ZeroMQ e MessagePack, mantendo o rastreio de relógios lógicos, offsets físicos e logs detalhados de transações e eventos de cluster.

Como Executar
Certifique-se de ter o Docker e o Docker Compose instalados.

Na raiz do projeto, execute:

Bash
docker compose up --build