"""Worker (processo 2): consulta a fila de tarefas no PostgreSQL.

Por enquanto só mantém o laço de consulta; a reserva e o pipeline entram na etapa 3
da ordem de implementação (docs/arquitetura-tcc.md, seção 9).
"""

import logging
import time

from lastro.config import obter_configuracao

logger = logging.getLogger("lastro.worker")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    configuracao = obter_configuracao()
    logger.info(
        "worker iniciado; intervalo de consulta: %ss", configuracao.worker_intervalo_consulta_s
    )
    try:
        while True:
            time.sleep(configuracao.worker_intervalo_consulta_s)
    except KeyboardInterrupt:
        logger.info("worker encerrado")


if __name__ == "__main__":
    main()
