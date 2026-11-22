# Aula 01 — Introdução ao NoSQL e MongoDB

## Objetivo

Entender as principais diferenças entre bancos de dados relacionais e não relacionais, conhecer o conceito de descasamento de impedância objeto-relacional e realizar as primeiras operações no MongoDB.

## Tecnologias utilizadas

- Python 3.14
- SQLite
- MongoDB 9.0.4
- PyMongo 4.20.1
- MongoDB Shell (mongosh)
- Ubuntu (WSL 2)
- Visual Studio Code

## Atividades realizadas

Nesta aula, utilizamos o código disponibilizado pelo professor para comparar duas formas de armazenar dados.

**1. Banco relacional (SQLite)**

Criamos quatro tabelas para armazenar informações de clientes, endereços, pedidos e produtos. Depois, utilizamos consultas com JOIN para reunir essas informações.

**2. Modelo não relacional (JSON)**

Organizamos os mesmos dados em um único documento JSON, com as informações do cliente e seus pedidos agrupados.

**3. MongoDB**

Conectamos o Python ao MongoDB utilizando a biblioteca PyMongo e realizamos operações de inserção, consulta e atualização de documentos.

Também utilizamos o `mongosh` para verificar os dados armazenados no banco.

## Como executar

O ambiente foi configurado no Ubuntu (WSL 2), utilizando o VS Code.

**1. Iniciar o MongoDB:**

```bash
sudo systemctl start mongod
```

**2. Ativar o ambiente virtual Python:**

```bash
source ~/ambientes-python/nosql-s6/bin/activate
```

**3. Instalar a biblioteca necessária (caso ainda não esteja instalada):**

```bash
python -m pip install pymongo
```

**4. Executar o programa na raiz do repositório:**

```bash
python Aula01/demonstracao_aula01.py
```

**5. Consultar os dados no MongoDB:**

```bash
mongosh
```

Dentro do MongoDB Shell:

```javascript
use ads_comercio
db.clientes.find().pretty()
```

## Resultados

A execução foi realizada com sucesso. Conseguimos inserir uma cliente com dois pedidos no MongoDB, consultar suas informações e adicionar um novo produto utilizando o operador `$push`.

A prática ajudou a entender como os documentos JSON podem organizar informações relacionadas e como essa estrutura se diferencia do modelo de tabelas do SQLite.

## Arquivos da aula

- `demonstracao_aula01.py` — Código prático disponibilizado pelo professor.
- `exercicios/respostas.md` — Respostas dos exercícios de fixação da Aula 01.

## Referência

Material da disciplina de Bancos de Dados Não-Relacionais, ministrada pelo professor Reginaldo Fernandes — IFCE Campus Tauá, semestre 2026.2.