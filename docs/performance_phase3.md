# Fase 3 � Cache e redu��o de chamadas ao Zabbix

## 1. Cache configurado no Django
- core/settings.py: adicionado CACHES com backend LocMemCache (timeout padr�o 60s) e CONN_MAX_AGE permanece 60.
- Optamos por cache em mem�ria local para validar rapidamente os ganhos; em produ��o recomenda-se substitui��o por Redis/Memcached.

## 2. Endpoints e fun��es cacheadas
- pi_fiber_cables agora usa cache.get/set com TTL de 30s.
- pi_device_ports idem (30s).
- _fetch_port_optical_snapshot armazena snapshots RX/TX por porta (30s) quando n�o h� discovery personalizado, reduzindo chamadas repetidas a item.get e history.get.
- efreshCableStatusValueMapped continua atualizando o InfoWindow; quando o cache expira, os dados s�o recarregados.

## 3. Resultados do profiling (MariaDB + cache)
`
python manage.py profile_endpoints --username=perf_tester --password=Perf#2025 --runs=5
`
- ibers: m�dia 1,6 ms / p95 4,8 ms
- sites: m�dia 1,7 ms / p95 2,3 ms
- device-ports: m�dia 7,7 ms / p95 34,3 ms *(antes: 33,4/35,5 ms)*
- port-optical-status: m�dia 252,1 ms / p95 1.253,5 ms *(antes: 351,4/1.749,6 ms)*
- iber-detail: m�dia 2,3 ms / p95 3,1 ms

Observa��es:
- A m�dia do endpoint port-optical-status reduziu significativamente; os picos remanescentes acontecem quando o cache expira e um novo item.get � necess�rio. Um cache distribu�do ou batch requests deve reduzir ainda mais o p95.
- Logs DEBUG em zabbix_api.services.zabbix_service seguem mostrando a dura��o de cada chamada ao Zabbix para monitoramento cont�nuo.

## 4. Pr�ximos passos
- Avaliar Redis/Memcached para cache compartilhado e estrat�gias de invalidation (ex.: quando cabos/portas forem atualizados).
- Implementar batch das consultas ao Zabbix (agrupar itemids) para mitigar picos.
- Considerar tarefas ass�ncronas (Celery/RQ) para pr�-coletar dados de tr�fego e hist�rico.
