#!/usr/bin/env python3
"""
Script para corrigir permissões do banco SQLite em Linux/Ubuntu.
Resolve o erro "attempt to write a readonly database".

Uso:
  python scripts/fix_db_permissions.py
  # ou, se precisar ajustar dono (requer sudo):
  sudo python scripts/fix_db_permissions.py --chown usuario:grupo
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Diretório do projeto (pai da pasta scripts)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent


def get_db_path() -> Path:
    """Obtém o caminho do banco a partir do .env ou usa o padrão."""
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                value = line.split("=", 1)[1].strip().strip('"\'')
                if value and "sqlite:///" in value:
                    path_str = value.split("sqlite:///")[-1].replace("\\", "/")
                    p = Path(path_str)
                    return p if p.is_absolute() else PROJECT_ROOT / p
    return PROJECT_ROOT / "data" / "saas_chatbot.db"


def main():
    parser = argparse.ArgumentParser(description="Corrige permissões do banco SQLite")
    parser.add_argument(
        "--chown",
        metavar="USER:GROUP",
        help="Ajusta dono do diretório e arquivo (ex: www-data:www-data). Requer sudo.",
    )
    args = parser.parse_args()

    db_path = get_db_path()
    data_dir = db_path.parent

    print(f"Diretório de dados: {data_dir}")
    print(f"Arquivo do banco:   {db_path}")

    # Cria diretório se não existir
    data_dir.mkdir(parents=True, exist_ok=True)
    print("  [OK] Diretório data/ garantido")

    # Permissões no Linux
    if sys.platform != "win32":
        try:
            os.chmod(data_dir, 0o755)
            print("  [OK] data/ com permissão 755")
        except OSError as e:
            print(f"  [AVISO] Não foi possível alterar permissão de data/: {e}")

        if db_path.exists():
            try:
                os.chmod(db_path, 0o664)
                print("  [OK] Banco com permissão 664")
            except OSError as e:
                print(f"  [AVISO] Não foi possível alterar permissão do banco: {e}")
        else:
            print("  [INFO] Arquivo do banco ainda não existe (será criado no primeiro acesso)")

        # chown se solicitado (usa comando do sistema)
        if args.chown:
            paths = [str(data_dir)]
            if db_path.exists():
                paths.append(str(db_path))
            try:
                subprocess.run(["chown", "-R", args.chown] + paths, check=True)
                print(f"  [OK] Dono ajustado para {args.chown}")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"  [ERRO] chown falhou: {e}")
                print("        Execute com: sudo python scripts/fix_db_permissions.py --chown usuario:grupo")
                sys.exit(1)
        else:
            print("\nSe o app rodar com outro usuário (ex: www-data), execute:")
            print(f"  sudo python scripts/fix_db_permissions.py --chown SEU_USUARIO:SEU_GRUPO")
    else:
        print("\n[INFO] Windows detectado - permissões não alteradas (não necessárias)")

    print("\nConcluído.")


if __name__ == "__main__":
    main()
