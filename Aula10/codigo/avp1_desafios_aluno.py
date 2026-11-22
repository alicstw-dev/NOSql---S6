#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
INSTITUTO FEDERAL DO CEARÁ -- CAMPUS TAUÁ
CURSO SUPERIOR DE TECNOLOGIA EM ANÁLISE E DESENVOLVIMENTO DE SISTEMAS (ADS)
COMPONENTE CURRICULAR: BANCO DE DADOS NÃO-RELACIONAIS (ADS16)
AVALIAÇÃO PRÁTICA 1 (AVP1) -- LABORATÓRIO N1 (17/11/2026)
Docente: Prof. Me. Reginaldo Pereira Fernandes
================================================================================

Nome do Discente / Dupla: ALICE MARIA DE LIMA MELO
Matrícula(s): 20241173010031

INSTRUÇÕES OBRIGATÓRIAS:
1. Certifique-se de que os containers do Redis e MongoDB estão em execução:
   $ docker compose up -d
2. Execute o script de povoamento prévio antes de iniciar:
   $ python povoar_ambiente_avp1.py
3. Complete o código de cada um dos 5 desafios nos blocos indicados por TODO.
4. Execute este script para rodar a suíte oficial de testes automatizados:
   $ python avp1_desafios_aluno.py
5. Cada desafio vale 2,0 pontos (Pontuação máxima: 10,0 pontos).
6. Prazo final de submissão: Domingo, 22/11/2026, até às 23h59 via Google Classroom da disciplina.
"""

import json
from datetime import datetime, timezone
import redis
from pymongo import MongoClient

def get_conexoes():
    """Retorna conexões ativas com as instâncias locais do Redis e MongoDB."""
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    m = MongoClient("mongodb://localhost:27017")
    db = m["ecommerce_shopgrids"]
    return r, db

# ==============================================================================
# DESAFIO 1 (Valor: 2,0 Pontos) -- Padrão Cache-Aside com TTL no Redis
# ==============================================================================
def buscar_produto_com_cache(r: redis.Redis, db, sku: str, ttl_segundos: int = 90) -> dict:
    
    chave = f"produto:{sku}"

    # Primeiro verifica se o produto já está no cache
    produto_cache = r.get(chave)

    if produto_cache:
        produto = json.loads(produto_cache)
        produto["_origem"] = "REDIS_CACHE"
        return produto

    # Caso não esteja no Redis, consulta o MongoDB
    produto = db.produtos.find_one({"sku": sku})

    if produto is None:
        return None

    # Converte os campos que não são serializáveis em JSON
    produto["_id"] = str(produto["_id"])
    produto["criado_em"] = produto["criado_em"].isoformat()

    for avaliacao in produto.get("avaliacoes", []):
        if "data" in avaliacao:
            avaliacao["data"] = avaliacao["data"].isoformat()

    # Salva o produto no Redis pelo tempo definido
    r.set(chave, json.dumps(produto, ensure_ascii=False), ex=ttl_segundos)

    produto["_origem"] = "MONGODB_RELOAD"
    return produto



# ==============================================================================
# DESAFIO 2 (Valor: 2,0 Pontos) -- Histórico de Itens Recentes com Listas Redis
# ==============================================================================
def registrar_historico_navegacao(r: redis.Redis, cliente_id: str, sku: str, max_itens: int = 5) -> list:
    
    # Define a chave do histórico do cliente
    chave = f"historico:{cliente_id}"

    # Remove o produto caso já esteja no histórico
    r.lrem(chave, 0, sku)

    # Adiciona o produto no início da lista
    r.lpush(chave, sku)

    # Mantém apenas os itens mais recentes
    r.ltrim(chave, 0, max_itens - 1)

    # Define o tempo de expiração de 15 minutos
    r.expire(chave, 900)

    # Retorna o histórico atualizado
    return r.lrange(chave, 0, -1)


# ==============================================================================
# DESAFIO 3 (Valor: 2,0 Pontos) -- Atualizações Atômicas de Arrays no MongoDB
# ==============================================================================
def adicionar_avaliacao_produto(db, sku: str, cliente_id: str, nota: int, comentario: str) -> bool:
    
    # Verifica se a nota está entre 1 e 5
    if not isinstance(nota, int) or not 1 <= nota <= 5:
        return False

    # Cria a nova avaliação
    nova_avaliacao = {
        "cliente_id": cliente_id,
        "nota": nota,
        "comentario": comentario,
        "data": datetime.now(timezone.utc)
    }

    # Adiciona a avaliação e incrementa o contador
    resultado = db.produtos.update_one(
        {"sku": sku},
        {
            "$push": {"avaliacoes": nova_avaliacao},
            "$inc": {"total_avaliacoes": 1}
        }
    )

    # Verifica se encontrou o produto
    if resultado.matched_count == 0:
        return False

    # Busca as avaliações atualizadas
    produto = db.produtos.find_one({"sku": sku})

    avaliacoes = produto.get("avaliacoes", [])

    # Calcula a nova média
    soma_notas = sum(avaliacao["nota"] for avaliacao in avaliacoes)
    media = round(soma_notas / len(avaliacoes), 2)

    # Atualiza a média no MongoDB
    db.produtos.update_one(
        {"sku": sku},
        {"$set": {"media_avaliacoes": media}}
    )

    return True


# ==============================================================================
# DESAFIO 4 (Valor: 2,0 Pontos) -- Indexação Otimizada pela Regra ESR
# ==============================================================================
def criar_indice_pedidos_esr(db) -> str:
   
    nome_indice = "idx_pedidos_esr_status_data_valor"

    # Cria o índice composto seguindo a regra ESR
    resultado = db.pedidos.create_index(
        [
            ("status", 1),
            ("data_pedido", -1),
            ("valor_total", 1)
        ],
        name=nome_indice
    )

    return resultado

# ==============================================================================
# DESAFIO 5 (Valor: 2,0 Pontos) -- Pipeline de Agregação de Vendas
# ==============================================================================
def relatorio_vendas_por_categoria(db) -> list:
   
    pipeline = [
        # Seleciona apenas pedidos entregues
        {
            "$match": {
                "status": "ENTREGUE"
            }
        },

        # Separa os itens dos pedidos
        {
            "$unwind": "$itens"
        },

        # Agrupa os valores por categoria
        {
            "$group": {
                "_id": "$itens.categoria",
                "faturamento_total": {
                    "$sum": "$itens.subtotal"
                },
                "quantidade_total": {
                    "$sum": "$itens.quantidade"
                },
                "ticket_medio_item": {
                    "$avg": "$itens.preco_unitario"
                }
            }
        },

        # Organiza os campos do relatório
        {
            "$project": {
                "_id": 0,
                "categoria": "$_id",
                "faturamento_total": {
                    "$round": ["$faturamento_total", 2]
                },
                "quantidade_total": 1,
                "ticket_medio_item": {
                    "$round": ["$ticket_medio_item", 2]
                }
            }
        },

        # Ordena pelo maior faturamento
        {
            "$sort": {
                "faturamento_total": -1
            }
        }
    ]

    # Executa o pipeline e retorna uma lista
    return list(db.pedidos.aggregate(pipeline))


# ==============================================================================
# SUÍTE DE TESTES AUTOMATIZADOS (Validação em Laboratório)
# ==============================================================================
def executar_testes():
    print("=" * 75)
    print("IFCE CAMPUS TAUÁ -- BANCO DE DADOS NÃO-RELACIONAIS")
    print("SUÍTE DE AVALIAÇÃO AUTOMATIZADA: AVP1 (LABORATÓRIO N1)")
    print("=" * 75)
    
    try:
        r, db = get_conexoes()
        r.ping()
        db.command("ping")
    except Exception as e:
        print(f"❌ Falha de Conexão com os Bancos: {e}")
        print("Certifique-se de subir o docker compose e executar o povoamento prévio.")
        return

    pontuacao_total = 0.0
    resultados = []

    # Teste 1: Cache-Aside
    print("\n[Executando Teste 1] Padrão Cache-Aside no Redis...")
    try:
        r.delete("produto:SKU-1001")
        # 1ª busca: deve ser Cache Miss
        p1 = buscar_produto_com_cache(r, db, "SKU-1001", ttl_segundos=60)
        assert p1 is not None, "Produto SKU-1001 deveria existir no MongoDB."
        assert p1.get("_origem") == "MONGODB_RELOAD", "Primeira busca deveria ter origem MONGODB_RELOAD."
        assert r.exists("produto:SKU-1001"), "Chave deveria ter sido gravada no Redis."
        ttl = r.ttl("produto:SKU-1001")
        assert 0 < ttl <= 60, f"TTL inválido: {ttl}."

        # 2ª busca: deve ser Cache Hit
        p2 = buscar_produto_com_cache(r, db, "SKU-1001", ttl_segundos=60)
        assert p2.get("_origem") == "REDIS_CACHE", "Segunda busca deveria ter origem REDIS_CACHE."
        
        # Busca inexistente
        p_inexistente = buscar_produto_com_cache(r, db, "SKU-INEXISTENTE-9999")
        assert p_inexistente is None, "Produto inexistente deveria retornar None."

        print("✔ Desafio 1 APROVADO (+2,0 Pontos)")
        pontuacao_total += 2.0
        resultados.append(("Desafio 1 (Cache-Aside Redis)", "APROVADO", 2.0))
    except Exception as e:
        print(f"❌ Desafio 1 FALHOU: {e}")
        resultados.append(("Desafio 1 (Cache-Aside Redis)", f"FALHOU ({e})", 0.0))

    # Teste 2: Histórico de Navegação
    print("\n[Executando Teste 2] Histórico de Navegação com Listas no Redis...")
    try:
        cid = "CLI-TESTE-999"
        r.delete(f"historico:{cid}")
        
        registrar_historico_navegacao(r, cid, "SKU-1001", max_itens=3)
        registrar_historico_navegacao(r, cid, "SKU-1002", max_itens=3)
        registrar_historico_navegacao(r, cid, "SKU-1003", max_itens=3)
        
        # Inserção duplicada de SKU-1001: deve subir para a cabeça sem duplicar
        h1 = registrar_historico_navegacao(r, cid, "SKU-1001", max_itens=3)
        assert h1 == ["SKU-1001", "SKU-1003", "SKU-1002"], f"Ordem incorreta após re-visita: {h1}"
        
        # Inserção que excede max_itens=3
        h2 = registrar_historico_navegacao(r, cid, "SKU-1004", max_itens=3)
        assert len(h2) == 3, f"Lista deveria ter no máximo 3 itens, obtido {len(h2)}"
        assert h2 == ["SKU-1004", "SKU-1001", "SKU-1003"], f"Ordem incorreta após LTRIM: {h2}"
        
        ttl_hist = r.ttl(f"historico:{cid}")
        assert 0 < ttl_hist <= 900, "TTL do histórico não foi configurado corretamente."

        print("✔ Desafio 2 APROVADO (+2,0 Pontos)")
        pontuacao_total += 2.0
        resultados.append(("Desafio 2 (Histórico Listas Redis)", "APROVADO", 2.0))
    except Exception as e:
        print(f"❌ Desafio 2 FALHOU: {e}")
        resultados.append(("Desafio 2 (Histórico Listas Redis)", f"FALHOU ({e})", 0.0))

    # Teste 3: Atualizações Atômicas no MongoDB
    print("\n[Executando Teste 3] Atualizações Atômicas de Arrays no MongoDB...")
    try:
        sku_alvo = "SKU-1002"
        doc_antes = db.produtos.find_one({"sku": sku_alvo})
        tot_antes = doc_antes.get("total_avaliacoes", 0)
        
        ok = adicionar_avaliacao_produto(db, sku_alvo, "CLI-200", 4, "Muito bom produto!")
        assert ok is True, "Função deveria retornar True para produto existente."
        
        doc_depois = db.produtos.find_one({"sku": sku_alvo})
        assert doc_depois["total_avaliacoes"] == tot_antes + 1, "total_avaliacoes não foi incrementado."
        assert len(doc_depois["avaliacoes"]) == tot_antes + 1, "Array avaliacoes não recebeu novo subdocumento."
        
        notas = [av["nota"] for av in doc_depois["avaliacoes"]]
        media_esperada = round(sum(notas) / len(notas), 2)
        assert abs(doc_depois["media_avaliacoes"] - media_esperada) < 0.01, f"Média incorreta: esperada {media_esperada}, obtida {doc_depois['media_avaliacoes']}"
        
        # Teste com SKU inexistente
        assert adicionar_avaliacao_produto(db, "SKU-NAO-EXISTE", "CLI-1", 5, "x") is False

        print("✔ Desafio 3 APROVADO (+2,0 Pontos)")
        pontuacao_total += 2.0
        resultados.append(("Desafio 3 (CRUD Atômico MongoDB)", "APROVADO", 2.0))
    except Exception as e:
        print(f"❌ Desafio 3 FALHOU: {e}")
        resultados.append(("Desafio 3 (CRUD Atômico MongoDB)", f"FALHOU ({e})", 0.0))

    # Teste 4: Regra ESR
    print("\n[Executando Teste 4] Criação e Validação de Índice Composto ESR...")
    try:
        nome_idx = criar_indice_pedidos_esr(db)
        assert nome_idx == "idx_pedidos_esr_status_data_valor", f"Nome do índice incorreto: {nome_idx}"
        
        indices = db.pedidos.index_information()
        assert "idx_pedidos_esr_status_data_valor" in indices, "Índice não encontrado na coleção pedidos."
        
        campos_idx = indices["idx_pedidos_esr_status_data_valor"]["key"]
        esperado = [("status", 1), ("data_pedido", -1), ("valor_total", 1)]
        assert campos_idx == esperado, f"Campos ou ordenação ESR incorretos: {campos_idx}"
        
        # Validação do plano de execução via explain()
        plan = db.pedidos.find(
            {"status": "ENTREGUE", "valor_total": {"$gte": 50.0}}
        ).sort({"data_pedido": -1}).explain()
        
        stages_str = json.dumps(plan)
        assert "IXSCAN" in stages_str, "O plano de execução deveria utilizar IXSCAN."
        assert "idx_pedidos_esr_status_data_valor" in stages_str, "O plano não utilizou o índice ESR criado."

        print("✔ Desafio 4 APROVADO (+2,0 Pontos)")
        pontuacao_total += 2.0
        resultados.append(("Desafio 4 (Índice Composto ESR)", "APROVADO", 2.0))
    except Exception as e:
        print(f"❌ Desafio 4 FALHOU: {e}")
        resultados.append(("Desafio 4 (Índice Composto ESR)", f"FALHOU ({e})", 0.0))

    # Teste 5: Aggregation Pipeline
    print("\n[Executando Teste 5] Pipeline de Agregação de Vendas por Categoria...")
    try:
        rel = relatorio_vendas_por_categoria(db)
        assert isinstance(rel, list), "O relatório de agregação deve retornar uma lista."
        assert len(rel) > 0, "O pipeline retornou uma lista vazia."
        
        primeiro = rel[0]
        chaves_esperadas = {"categoria", "faturamento_total", "quantidade_total", "ticket_medio_item"}
        assert set(primeiro.keys()) == chaves_esperadas, f"Campos incorretos no documento agregado: {primeiro.keys()}"
        
        # Validar ordenação decrescente de faturamento
        faturamentos = [item["faturamento_total"] for item in rel]
        assert faturamentos == sorted(faturamentos, reverse=True), "O resultado não está ordenado por faturamento_total decrescente."

        print("✔ Desafio 5 APROVADO (+2,0 Pontos)")
        pontuacao_total += 2.0
        resultados.append(("Desafio 5 (Pipeline Aggregation)", "APROVADO", 2.0))
    except Exception as e:
        print(f"❌ Desafio 5 FALHOU: {e}")
        resultados.append(("Desafio 5 (Pipeline Aggregation)", f"FALHOU ({e})", 0.0))

    # Relatório Final
    print("\n" + "=" * 75)
    print("QUADRO RESUMO DE PONTUAÇÃO FINAL:")
    print("=" * 75)
    for desc, st, pt in resultados:
        print(f"  * {desc:<38} : {st:<18} [{pt:.1f} / 2.0 pts]")
    print("-" * 75)
    print(f"  NOTA FINAL OBTIDA NA AVP1: {pontuacao_total:.1f} / 10.0 PONTOS")
    print("=" * 75)

if __name__ == "__main__":
    executar_testes()
