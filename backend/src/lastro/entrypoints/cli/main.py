"""Terminal do Lastro: análise local e replay histórico."""

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lastro", description="Documentação viva de regras de negócio."
    )
    subcomandos = parser.add_subparsers(dest="comando", required=True)

    analisar = subcomandos.add_parser("analisar", help="Compara duas versões de um arquivo Python.")
    analisar.add_argument("base", help="Arquivo na versão anterior.")
    analisar.add_argument("novo", help="Arquivo na versão nova.")

    args = parser.parse_args(argv)
    if args.comando == "analisar":
        print("analisador ainda não implementado (etapa 1)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
