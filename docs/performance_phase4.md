# Fase 4 � Tarefas ass�ncronas e pr�-aquecimento de cache

## 1. Celery configurado
- Adicionadas depend�ncias (`celery==5.4.0`) e criado `core/celery.py` com autodiscovery de tasks.
- `core/__init__.py` exp�e `celery_app` para que `celery -A core worker -l info` funcione.
- Ajustes em `core/settings.py`:
  - `CELERY_BROKER_URL` e `CELERY_RESULT_BACKEND` apontam para o Redis (`redis://127.0.0.1:6379/0`).
  - Serializadores e fila padr�o definidos para JSON (`mapspro_default`).

## 2. Tarefas de pr�-aquecimento (`zabbix_api/tasks.py`)
- `warm_port_optical_cache(port_id)` � revalida e grava no cache o snapshot RX/TX da porta.
- `warm_device_ports(device_id)` � percorre todas as portas do dispositivo.
- `warm_all_optical_snapshots()` � enfileira `warm_port_optical_cache` para todas as portas monitoradas.

## 3. Comando de gerenciamento
```
python manage.py warm_optical_cache [--device-id=<id>] [--async]
```
- Sem `--async` executa inline (bom para pr�-aquecer manualmente ap�s o deploy).
- Com `--async` envia as tarefas para o Celery (`warm_port_optical_cache.delay`).
- Exemplo de uso: `python manage.py warm_optical_cache --async` + `celery -A core worker -l info`.

## 4. Resultados p�s-aquecimento + Redis
- Ap�s executar `warm_optical_cache` e manter o Redis ativo, o profiling indicou:
  - `port-optical-status`: m�dia ~286 ms / p95 ~1.420 ms (queda adicional na m�dia em rela��o � fase anterior gra�as ao cache populado).
  - Demais endpoints mantiveram m�dia <10 ms.
- Rodar o aquecimento periodicamente (via Celery beat ou cron) mant�m o cache preenchido e evita que usu�rios paguem a primeira consulta cara.

## 5. Pr�ximos passos sugeridos
- Configurar um scheduler (Celery Beat/cron) para chamar `warm_all_optical_snapshots` a cada X minutos.
- Monitorar o worker e o Redis (m�tricas, `redis-cli monitor`).
- Evoluir `port-optical-status` para usar batch de `itemids` se os picos continuarem elevados.
