#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Carga e Povoamento do Ambiente de Testes da AVP1 (Laboratório N1)
Componente Curricular: Banco de Dados Não-Relacionais (ADS16) - IFCE Campus Tauá
Docente: Prof. Me. Reginaldo Pereira Fernandes
Data de Aplicação: 17/11/2026 (Aula 10)

Objetivo:
Gera e carrega uma base representativa do e-commerce ShopGrids no MongoDB local
(`ecommerce_shopgrids`) e limpa as chaves transitórias no Redis local para que
o discente inicie a avaliação prática com um ambiente 100% determinístico e limpo.
"""

import json
import random
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
import redis

# Configurações de Conexão
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "ecommerce_shopgrids"
REDIS_HOST = "localhost"
REDIS_PORT = 6379

CATEGORIAS = [
    "Eletrônicos", "Informática", "Livros & Cultura", 
    "Eletrodomésticos", "Esporte & Lazer", "Casa & Decoração"
]

NOMES_PRODUTOS = {
    "Eletrônicos": ["Smartphone Galaxy Ultra", "Smart TV 55 4K", "Fone Bluetooth Noise Cancelling", "Soundbar Surround"],
    "Informática": ["Notebook Pro 16GB", "Monitor Ultrawide 29", "Teclado Mecânico RGB", "Mouse Ergonômico Sem Fio"],
    "Livros & Cultura": ["Guia NoSQL Prático", "Arquitetura Limpa", "O Programador Pragmático", "Microsserviços na Prática"],
    "Eletrodomésticos": ["Fritadeira Air Fryer 4L", "Cafeteira Espresso Automática", "Liquidificador Turbo", "Micro-ondas Inox 32L"],
    "Esporte & Lazer": ["Bicicleta Mountain Bike Aro 29", "Tênis de Corrida Amortecido", "Kit Halteres Ajustáveis", "Mochila Impermeável"],
    "Casa & Decoração": ["Cadeira de Escritório Ergonômica", "Mesa Ajustável de Altura", "Luminária Inteligente LED", "Jogo de Lençol 400 Fios"]
}

STATUS_PEDIDO = ["CRIADO", "PAGO", "EM_TRANSPORTE", "ENTREGUE", "CANCELADO"]

def povoar_ambiente():
    print("=" * 70)
    print("IFCE Campus Tauá -- AVP1 Banco de Dados Não-Relacionais")
    print("Inicializando carga de dados de teste (MongoDB + Redis)...")
    print("=" * 70)

    # 1. Conexão e Reset do Redis
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        r.flushdb()
        print("✔ Redis conectado em localhost:6379 e cache reinicializado (FLUSHDB executado).")
    except Exception as e:
        print(f"⚠ Aviso Redis: Não foi possível conectar ao Redis ({e}). Certifique-se de que o container está ativo.")

    # 2. Conexão e Reset do MongoDB
    try:
        m = MongoClient(MONGO_URI)
        m.admin.command("ping")
        db = m[DB_NAME]
        
        # Remove coleções anteriores para garantir idempotência
        db.produtos.drop()
        db.clientes.drop()
        db.pedidos.drop()
        print(f"✔ MongoDB conectado em localhost:27017 (`{DB_NAME}`). Coleções anteriores limpas.")
    except Exception as e:
        print(f"❌ Erro fatal ao conectar no MongoDB: {e}")
        return

    # 3. Povoamento da Coleção 'produtos'
    produtos = []
    sku_counter = 1000
    for cat, lista_nomes in NOMES_PRODUTOS.items():
        for nome in lista_nomes:
            sku_counter += 1
            sku = f"SKU-{sku_counter}"
            preco = round(random.uniform(49.90, 3499.00), 2)
            estoque = random.randint(10, 150)
            produtos.append({
                "sku": sku,
                "nome": nome,
                "categoria": cat,
                "preco": preco,
                "estoque": estoque,
                "ativo": True,
                "avaliacoes": [
                    {
                        "cliente_id": "CLI-101",
                        "nota": 5,
                        "comentario": "Excelente qualidade e entrega rápida!",
                        "data": datetime.now(timezone.utc) - timedelta(days=random.randint(5, 30))
                    }
                ],
                "total_avaliacoes": 1,
                "media_avaliacoes": 5.0,
                "tags": [cat.lower(), "shopgrids", "destaque"],
                "criado_em": datetime.now(timezone.utc) - timedelta(days=random.randint(30, 180))
            })
    
    db.produtos.insert_many(produtos)
    db.produtos.create_index("sku", unique=True)
    print(f"✔ Coleção 'produtos': {len(produtos)} produtos cadastrados com índice único em 'sku'.")

    # 4. Povoamento da Coleção 'clientes'
    clientes = []
    for i in range(1, 41):
        cid = f"CLI-{100 + i}"
        clientes.append({
            "cliente_id": cid,
            "nome": f"Cliente Exemplo {i}",
            "email": f"cliente{i}@exemplo.com.br",
            "cidade": random.choice(["Tauá", "Fortaleza", "Juazeiro do Norte", "Sobral", "Crateús", "Iguatu"]),
            "uf": "CE",
            "ativo": True,
            "data_cadastro": datetime.now(timezone.utc) - timedelta(days=random.randint(60, 360))
        })
    db.clientes.insert_many(clientes)
    db.clientes.create_index("cliente_id", unique=True)
    print(f"✔ Coleção 'clientes': {len(clientes)} clientes cadastrados.")

    # 5. Povoamento da Coleção 'pedidos'
    pedidos = []
    lista_skus = [p["sku"] for p in produtos]
    skus_dict = {p["sku"]: p for p in produtos}
    
    for i in range(1, 151):
        pid = f"PED-{5000 + i}"
        cliente = random.choice(clientes)
        status = random.choice(STATUS_PEDIDO)
        data_pedido = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60), hours=random.randint(1, 23))
        
        # 1 a 4 itens por pedido
        qtd_itens = random.randint(1, 3)
        skus_escolhidos = random.sample(lista_skus, qtd_itens)
        itens = []
        valor_total = 0.0
        
        for sku in skus_escolhidos:
            prod_info = skus_dict[sku]
            qtd = random.randint(1, 4)
            subtotal = round(prod_info["preco"] * qtd, 2)
            valor_total += subtotal
            itens.append({
                "sku": sku,
                "nome_produto": prod_info["nome"],
                "categoria": prod_info["categoria"],
                "preco_unitario": prod_info["preco"],
                "quantidade": qtd,
                "subtotal": subtotal
            })
            
        valor_total = round(valor_total, 2)
        
        pedidos.append({
            "pedido_id": pid,
            "cliente_id": cliente["cliente_id"],
            "status": status,
            "data_pedido": data_pedido,
            "itens": itens,
            "valor_total": valor_total,
            "metodo_pagamento": random.choice(["PIX", "CARTAO_CREDITO", "BOLETO"])
        })
        
    db.pedidos.insert_many(pedidos)
    print(f"✔ Coleção 'pedidos': {len(pedidos)} pedidos cadastrados.")
    print("=" * 70)
    print("Carga de testes concluída com sucesso! Ambiente pronto para AVP1.")
    print("=" * 70)

if __name__ == "__main__":
    povoar_ambiente()
