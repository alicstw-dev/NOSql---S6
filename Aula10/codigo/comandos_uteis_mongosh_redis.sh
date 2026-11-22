#!/usr/bin/env bash
# ==============================================================================
# IFCE CAMPUS TAUÁ -- BANCO DE DADOS NÃO-RELACIONAIS (ADS16)
# GUIA RÁPIDO DE COMANDOS CLI: AVP1 (LABORATÓRIO N1)
# ==============================================================================

echo "=== 1. Conexão aos Terminais Interativos ==="
# Acessar terminal do Redis via container Docker
docker exec -it shopgrids-redis-avp1 redis-cli

# Acessar terminal do MongoDB (MongoSH) via container Docker
docker exec -it shopgrids-mongodb-avp1 mongosh ecommerce_shopgrids

echo "=== 2. Comandos Essenciais do Redis (redis-cli) ==="
# Testar conexão
# PING

# Consultar chaves de produto em cache
# KEYS produto:*
# GET produto:SKU-1001
# TTL produto:SKU-1001

# Inspecionar listas de histórico de navegação
# KEYS historico:*
# LRANGE historico:CLI-101 0 -1
# LLEN historico:CLI-101
# TTL historico:CLI-101

# Limpar o banco de dados do Redis
# FLUSHDB

echo "=== 3. Comandos Essenciais do MongoDB (mongosh) ==="
# Alternar para o banco correto
# use ecommerce_shopgrids

# Consultar produtos e subdocumentos
# db.produtos.findOne({ sku: "SKU-1001" })
# db.produtos.countDocuments()

# Inspecionar índices criados
# db.pedidos.getIndexes()

# Analisar plano de execução (Verificar IXSCAN)
# db.pedidos.find({ status: "ENTREGUE", valor_total: { $gte: 100 } }).sort({ data_pedido: -1 }).explain("executionStats")

# Testar pipeline analítico interativamente no MongoSH
# db.pedidos.aggregate([
#   { $match: { status: "ENTREGUE" } },
#   { $unwind: "$itens" },
#   { $group: {
#       _id: "$itens.categoria",
#       faturamento_total: { $sum: "$itens.subtotal" },
#       quantidade_total: { $sum: "$itens.quantidade" }
#   }},
#   { $sort: { faturamento_total: -1 } }
# ])
