# Fase 2 � Migra��o para MariaDB e Ajustes de Banco

## 1. Configura��o do MariaDB
- Servidor local: `C:\Program Files\MariaDB 12.0` com servi�o `MariaDB` em execu��o.
- Banco criado: `mapspro_db` (charset `utf8mb4`) e usu�rio `mapspro_user` com senha `Maps@Prove#2025`.
- Banco de testes (`test_mapspro_db`) tamb�m provisionado para suportar a su�te Django.

## 2. Ajustes no projeto
- `core/settings.py` atualizado para usar MariaDB como `default` e manter o SQLite como `legacy` � facilita consultas/dumps do banco antigo.
- Depend�ncia `PyMySQL` adicionada (`requirements.txt`), com `pymysql.install_as_MySQLdb()` em `core/__init__.py` para compatibilidade.

## 3. Migra��o dos dados
1. Dump do SQLite usando o alias `legacy`:
   ```bash
   python manage.py dumpdata --database=legacy \
       --natural-foreign --natural-primary \
       --exclude=contenttypes --exclude=auth.permission \
       --exclude=sessions.session --exclude=admin.logentry \
       --indent 2 --output data/sqlite_dump.json
   ```
2. Recria��o do banco MariaDB (drop + migrate) e importa��o:
   ```bash
   mysql -u root -p -e "DROP DATABASE IF EXISTS mapspro_db; DROP DATABASE IF EXISTS test_mapspro_db; CREATE DATABASE mapspro_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
   python manage.py migrate
   python manage.py loaddata data/sqlite_dump.json
   ```
3. Usu�rio `perf_tester` recriado ap�s o load para garantir credenciais de teste (`Perf#2025`).

## 4. �ndices e logging
- �ndices criados em colunas usadas com frequ�ncia:
  ```sql
  CREATE INDEX idx_port_device ON zabbix_api_port (device_id);
  CREATE INDEX idx_fiber_origin_port ON zabbix_api_fibercable (origin_port_id);
  CREATE INDEX idx_fiber_destination_port ON zabbix_api_fibercable (destination_port_id);
  CREATE INDEX idx_fiberevent_fiber ON zabbix_api_fiberevent (fiber_id);
  ```
- Slow query log ativado no MariaDB:
  ```sql
  SET GLOBAL slow_query_log = 'ON';
  SET GLOBAL long_query_time = 0.5;
  ```
  (Arquivo padr�o `hostname-slow.log` em `C:/Program Files/MariaDB 12.0/data/`.)

## 5. Valida��o
- `python manage.py profile_endpoints --username=perf_tester --password=Perf#2025 --runs=5`
  - Resultados atuais (ms): `fibers` avg 2.5/p95 5.3, `device-ports` avg 33.4/p95 35.5, `port-optical-status` avg 1794/p95 1871, `fiber-detail` avg 3.0/p95 4.2.
  - Logs de debug mostram chamadas `item.get` ~600 ms cada � alvo para otimiza��es na Fase 3.
- `python manage.py test tests` � 23 testes passando contra MariaDB.

## 6. Pr�ximos passos
- Implementar cache/batch para consultas ao Zabbix (especialmente `port-optical-status`).
- Avaliar Redis/Memcached para endpoints `/api/fibers/` e `/api/device-ports/`.
- Ajustar `CONN_MAX_AGE` conforme comportamento em prod e monitorar slow query log para identificar novos gargalos.
