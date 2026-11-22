# Aula 01 — Lista de Exercícios 1 (Bloco 1)

**Disciplina:** Banco de Dados Não-Relacionais  
**Tema:** Introdução ao NoSQL e MongoDB

### 1. Por que os bancos relacionais enfrentam dificuldades para escalar horizontalmente mantendo propriedades ACID estritas?

Porque precisam garantir que os dados continuem corretos e consistentes, mesmo estando em servidores diferentes. Isso exige mais comunicação e sincronização entre os servidores, o que pode deixar as operações mais lentas e complexas.

### 2. O que é Descasamento de Impedância Objeto-Relacional e como o modelo de documentos reduz esse problema?

É a diferença entre a forma como os dados são organizados nos objetos de uma aplicação e nas tabelas de um banco relacional. No modelo de documentos, podemos guardar informações relacionadas em um único documento, evitando várias tabelas e consultas com JOIN.

### 3. Quais são as diferenças entre Scale-Up e Scale-Out?

**Scale-Up** é melhorar a capacidade de um servidor, aumentando memória e processamento. É mais simples, mas pode ficar caro e tem limites físicos.

**Scale-Out** é adicionar mais servidores para dividir o trabalho. Permite crescer de forma mais flexível, mas exige maior controle da distribuição dos dados.

### 4. O que é Network Shuffle em consultas com múltiplos JOINs em clusters particionados?

É quando os servidores precisam trocar dados pela rede para realizar consultas que envolvem informações armazenadas em lugares diferentes. Essa movimentação pode aumentar bastante o tempo das consultas.

### 5. Qual é a diferença entre bancos orientados a agregados e não orientados a agregados?

Os bancos orientados a agregados agrupam dados relacionados em uma mesma unidade, como acontece com documentos no MongoDB.

Já os não orientados a agregados trabalham com informações e relacionamentos de forma mais independente, como nos bancos de grafos.

### 6. Como inicializar e verificar o serviço MongoDB no Ubuntu ou Windows?

No **Ubuntu**, podemos iniciar o MongoDB com:

`sudo systemctl start mongod`

E verificar se está funcionando com:

`sudo systemctl status mongod`

No **Windows**, podemos usar o PowerShell como administrador:

`Start-Service MongoDB`

Para verificar:

`Get-Service MongoDB`

Também podemos testar a conexão usando o `mongosh` e o comando `db.runCommand({ ping: 1 })`.