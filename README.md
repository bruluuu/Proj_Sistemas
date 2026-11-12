# Projeto Sistemas Distribuídos - Parte 1

Protótipo de chat distribuído implementando comunicação baseada em sockets ZeroMQ, persistência relacional e arquitetura containerizada via Docker Compose.

## Escolhas Tecnológicas

* **Linguagens:** 
  * **Python (Servidor):** Escolhido pela facilidade e robustez na manipulação de sockets ZeroMQ e integração nativa com bancos de dados relacionais.
  * **Java (Cliente/Bot):** Utilizado para simular os bots clientes, garantindo o requisito de uso de duas linguagens diferentes no projeto individual.
* **Serialização:** 
  * **MessagePack:** Utilizado para realizar a serialização binária das mensagens entre cliente e servidor, atendendo à restrição de não utilizar formatos de texto simples (como JSON ou XML) e incluindo o timestamp obrigatório de envio.
* **Persistência de Dados:** 
  * **PostgreSQL:** Cada servidor possui sua própria instância isolada de banco de dados em disco (com volumes Docker independentes), armazenando os nomes de usuários com seus respectivos timestamps de login e os canais criados.

## Como Executar

Para subir todo o ambiente simulando múltiplos servidores e clientes em execução paralela, execute o comando na raiz do projeto:

```bash
docker compose up --build