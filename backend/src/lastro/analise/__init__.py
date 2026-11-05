"""Núcleo estático com `ast`: extrai estruturas, compara versões, calcula dependências e seleciona
contexto.

Módulo puro (sem adapters): recebe texto de código e devolve resultados estruturados.
Reutilizado pelo worker, pelo terminal e pelo replay.
"""
