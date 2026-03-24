#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de backup do sistema Urânia +
Faz backup completo: banco de dados e documentos em arquivo compactado
"""
import os
import sys
import shutil
import tarfile
import json
from pathlib import Path
from datetime import datetime

# Corrige encoding no Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

def safe_print(text):
    """Imprime texto de forma segura, removendo emojis se necessário"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Remove emojis e caracteres especiais se houver problema de encoding
        import re
        text_clean = re.sub(r'[^\x00-\x7F]+', '', text)
        print(text_clean)

def get_backup_dir() -> Path:
    """Retorna o diretório de backups"""
    # Tenta criar no diretório do projeto primeiro
    project_root = Path(__file__).parent.parent
    backup_dir = project_root / "backups"
    
    # Tenta criar o diretório com tratamento de erro
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # Se não tiver permissão, tenta criar em um diretório temporário do usuário
        import tempfile
        user_backup_dir = Path(tempfile.gettempdir()) / "urania_backups"
        try:
            user_backup_dir.mkdir(parents=True, exist_ok=True)
            safe_print(f"AVISO: Sem permissão para criar em {backup_dir}")
            safe_print(f"Usando diretório alternativo: {user_backup_dir}")
            return user_backup_dir
        except Exception as e:
            # Último recurso: usa diretório atual
            safe_print(f"AVISO: Erro ao criar diretório de backup: {e}")
            safe_print(f"Usando diretório atual: {Path.cwd()}")
            return Path.cwd() / "backups"
    except Exception as e:
        # Se houver outro erro, tenta diretório temporário
        import tempfile
        user_backup_dir = Path(tempfile.gettempdir()) / "urania_backups"
        try:
            user_backup_dir.mkdir(parents=True, exist_ok=True)
            safe_print(f"AVISO: Erro ao criar diretório de backup: {e}")
            safe_print(f"Usando diretório alternativo: {user_backup_dir}")
            return user_backup_dir
        except:
            # Se tudo falhar, usa diretório atual
            safe_print(f"AVISO: Não foi possível criar diretório de backup")
            safe_print(f"Usando diretório atual: {Path.cwd()}")
            return Path.cwd() / "backups"
    
    return backup_dir

def main():
    """Função principal - cria backup compactado"""
    safe_print("=" * 60)
    safe_print("Backup do Sistema Urania +")
    safe_print("=" * 60)
    safe_print("")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = get_backup_dir()
    output_file = backup_dir / f"urania_backup_{timestamp}.tar.gz"
    
    try:
        # 1. BACKUP DO BANCO DE DADOS
        safe_print("[1/3] Copiando banco de dados...")
        db_url = settings.database_url
        
        if not db_url.startswith("sqlite:///"):
            safe_print("AVISO: Banco de dados nao e SQLite. Backup manual necessario para PostgreSQL/MySQL.")
            db_path = None
        else:
            db_path = Path(db_url.replace("sqlite:///", ""))
            if not db_path.exists():
                safe_print(f"AVISO: Banco de dados nao encontrado: {db_path}")
                db_path = None
            else:
                size_mb = db_path.stat().st_size / (1024 * 1024)
                safe_print(f"   OK - Banco encontrado: {size_mb:.2f} MB")
        
        # 2. BACKUP DOS ARQUIVOS DE UPLOAD
        safe_print("[2/3] Copiando arquivos de upload...")
        upload_dir = settings.upload_dir_path
        
        pdf_count = 0
        gif_count = 0
        image_count = 0
        total_size = 0
        
        if upload_dir.exists():
            pdf_dir = upload_dir / "pdfs"
            gif_dir = upload_dir / "gifs"
            image_dir = upload_dir / "images"
            
            if pdf_dir.exists():
                pdf_count = len([f for f in pdf_dir.iterdir() if f.is_file()])
                for f in pdf_dir.iterdir():
                    if f.is_file():
                        total_size += f.stat().st_size
            
            if gif_dir.exists():
                gif_count = len([f for f in gif_dir.iterdir() if f.is_file()])
                for f in gif_dir.iterdir():
                    if f.is_file():
                        total_size += f.stat().st_size

            if image_dir.exists():
                image_count = len([f for f in image_dir.iterdir() if f.is_file()])
                for f in image_dir.iterdir():
                    if f.is_file():
                        total_size += f.stat().st_size
            
            safe_print(f"   OK - {pdf_count} PDFs, {gif_count} GIFs, {image_count} imagens ({total_size / 1024 / 1024:.2f} MB)")
        else:
            safe_print(f"   AVISO: Diretorio de uploads nao encontrado: {upload_dir}")
            upload_dir = None
        
        # 3. CRIAR ARQUIVO COMPACTADO
        safe_print("[3/3] Criando arquivo compactado...")
        
        with tarfile.open(output_file, "w:gz") as tar:
            # Adiciona banco de dados
            if db_path and db_path.exists():
                tar.add(db_path, arcname="database.db")
                safe_print("   OK - Banco de dados adicionado")
            
            # Adiciona arquivos de upload
            if upload_dir and upload_dir.exists():
                # Adiciona PDFs
                pdf_dir = upload_dir / "pdfs"
                if pdf_dir.exists():
                    for pdf_file in pdf_dir.iterdir():
                        if pdf_file.is_file():
                            tar.add(pdf_file, arcname=f"uploads/pdfs/{pdf_file.name}")
                
                # Adiciona GIFs
                gif_dir = upload_dir / "gifs"
                if gif_dir.exists():
                    for gif_file in gif_dir.iterdir():
                        if gif_file.is_file():
                            tar.add(gif_file, arcname=f"uploads/gifs/{gif_file.name}")

                image_dir = upload_dir / "images"
                if image_dir.exists():
                    for img_file in image_dir.iterdir():
                        if img_file.is_file():
                            tar.add(img_file, arcname=f"uploads/images/{img_file.name}")
                
                safe_print("   OK - Arquivos de upload adicionados")
            
            # Adiciona informações do backup
            backup_info = {
                "timestamp": timestamp,
                "app_name": settings.APP_NAME,
                "app_version": settings.APP_VERSION,
                "database_included": db_path is not None and db_path.exists(),
                "uploads_included": upload_dir is not None and upload_dir.exists(),
                "pdf_count": pdf_count,
                "gif_count": gif_count,
                "image_count": image_count,
                "total_size_bytes": total_size
            }
            
            import io
            info_json = json.dumps(backup_info, indent=2, ensure_ascii=False)
            info_bytes = io.BytesIO(info_json.encode('utf-8'))
            info_tarinfo = tarfile.TarInfo(name="backup_info.json")
            info_tarinfo.size = len(info_bytes.getvalue())
            tar.addfile(info_tarinfo, info_bytes)
            safe_print("   OK - Informacoes do backup adicionadas")
        
        # 4. RESULTADO FINAL
        final_size = output_file.stat().st_size / (1024 * 1024)
        safe_print("")
        safe_print("=" * 60)
        safe_print("BACKUP CONCLUIDO COM SUCESSO!")
        safe_print("=" * 60)
        safe_print(f"Arquivo: {output_file.name}")
        safe_print(f"Tamanho: {final_size:.2f} MB")
        safe_print(f"Banco de dados: {'Incluido' if db_path and db_path.exists() else 'Nao encontrado'}")
        safe_print(f"Documentos: {pdf_count} PDFs, {gif_count} GIFs, {image_count} imagens")
        safe_print("")
        safe_print(f"Para restaurar: python scripts/restore.py {output_file.name}")
        safe_print("=" * 60)
        
        return 0
        
    except Exception as e:
        safe_print("")
        safe_print("=" * 60)
        safe_print("ERRO AO CRIAR BACKUP")
        safe_print("=" * 60)
        safe_print(f"Erro: {e}")
        import traceback
        # Usa stderr para traceback (que já foi configurado com UTF-8)
        traceback.print_exc()
        
        # Remove arquivo parcial se existir
        if output_file.exists():
            try:
                output_file.unlink()
            except:
                pass
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
