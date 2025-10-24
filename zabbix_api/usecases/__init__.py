"""
Camada de orquestração que encapsula regras de negócio reutilizáveis.

Os módulos dentro de `zabbix_api.usecases` devem evitar lidar com HttpRequest
Diretamente, retornando dados brutos ou lançando exceções específicas.
"""

