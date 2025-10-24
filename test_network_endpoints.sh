#!/bin/bash

# Script para testar os novos endpoints de informa??es de rede
# Execute este script ap?s iniciar o servidor Django

BASE_URL="http://localhost:8000/zabbix_api"

echo "? Testando Endpoints de Informa??es de Rede"
echo "============================================="

echo ""
echo "1. ? Overall system status:"
curl -s "$BASE_URL/status/" | python3 -m json.tool

echo ""
echo "2. ?? Lista de hosts com informa??es de rede:"
curl -s "$BASE_URL/hosts/network-info/" | python3 -m json.tool

echo ""
echo "3. ? Informa??es detalhadas do primeiro host encontrado:"
# Primeiro, vamos obter a lista de hosts para pegar um hostid
HOSTID=$(curl -s "$BASE_URL/hosts/" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['hosts'][0]['hostid'] if data.get('hosts') else '')")

if [ ! -z "$HOSTID" ]; then
    echo "   Host ID encontrado: $HOSTID"
    curl -s "$BASE_URL/hosts/$HOSTID/network-info/" | python3 -m json.tool
else
    echo "   ? No host found"
fi

echo ""
echo "4. ?? Problemas cr?ticos:"
curl -s "$BASE_URL/problems/critical/" | python3 -m json.tool

echo ""
echo "5. ? Vis?o geral do monitoramento:"
curl -s "$BASE_URL/monitoring/overview/" | python3 -m json.tool

echo ""
echo "6. ? Hosts availability:"
curl -s "$BASE_URL/monitoring/availability/" | python3 -m json.tool

echo ""
echo "? Test complete!"
echo ""
echo "? Summary of tested endpoints:"
echo "   - Status geral: /status/"
echo "   - Network info (todos): /hosts/network-info/"
echo "   - Network info (espec?fico): /hosts/{hostid}/network-info/"
echo "   - Problemas cr?ticos: /problems/critical/"
echo "   - Vis?o geral: /monitoring/overview/"
echo "   - Disponibilidade: /monitoring/availability/"