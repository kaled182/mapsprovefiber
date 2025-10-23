# Fase 6 � Observabilidade e Monitoramento

## 1. M�tricas Prometheus
- Instalado django-prometheus e adicionado a INSTALLED_APPS / MIDDLEWARE.
- Nova rota GET /metrics/ (via core/urls.py) exp�e m�tricas padr�o do Django, Redis e MariaDB.
- Exemplo r�pido:
  `ash
  curl http://localhost:8000/metrics/ | head
  `
  Integre esse endpoint ao Prometheus/Grafana para dashboards de lat�ncia, cache hits e uso de tarefas Celery.

## 2. Logging estruturado
- Diret�rio logs/ criado automaticamente; RotatingFileHandler grava pplication.log (5 MB + 5 backups).
- Loggers principais (django, celery, zabbix_api, etc.) enviam para console e arquivo.
- Consultar em tempo real: 	ail -f logs/application.log.

## 3. Slow Query Inspector
- Novo comando: python manage.py show_slow_queries --path "C:\Program Files\MariaDB 12.0\data\<host>-slow.log" --limit 10
- Pode omitir --path se MYSQL_SLOW_LOG_PATH estiver definido.
- Sa�da inclui Query_time, Lock_time, linhas examinadas e o SQL completo para an�lise/EXPLAIN.

## 4. Pr�ximos passos sugeridos
- Conectar /metrics/ a um Prometheus/Grafana e definir alertas (lat�ncia alta, worker inativo, crescimento do log).
- Automatizar coleta do slow-log (cron + show_slow_queries ou parsing via Promtail/Loki).
- Avaliar integra��o com APM (Sentry, New Relic) para rastreamento de requisi��es Celery + HTTP.
