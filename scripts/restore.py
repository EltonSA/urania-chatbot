#!/usr/bin/env python3
"""
Script de restore do sistema Urânia +
Restaura backup completo: banco de dados e documentos
"""
import os
import sys
import shutil
import json
import tarfile
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database import init_db

def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("=" * 60)
        print("📦 Restore do Sistema Urânia +")
        print("=" * 60)
        print()
        print("Uso: python scripts/restore.py <arquivo_backup.tar.gz>")
        print()
        print("Exemplo:")
        print("  python scripts/restore.py backups/urania_backup_20251223_120000.tar.gz")
        print()
        return 1
    
    backup_file = Path(sys.argv[1])
    if not backup_file.is_absolute():
        # Tenta encontrar no diretório de backups
        backup_dir = Path(__file__).parent.parent / "backups"
        backup_file = backup_dir / backup_file.name
    
    if not backup_file.exists():
        print(f"❌ Arquivo de backup não encontrado: {backup_file}")
        return 1
    
    print("=" * 60)
    print("📦 Restore do Sistema Urânia +")
    print("=" * 60)
    print(f"Arquivo: {backup_file.name}")
    print()
    
    try:
        # 1. EXTRAIR ARQUIVO
        print("📂 Extraindo arquivo de backup...")
        extract_dir = Path(__file__).parent.parent / "backups" / "restore_temp"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        with tarfile.open(backup_file, "r:gz") as tar:
            tar.extractall(extract_dir)
        
        print("   ✅ Arquivo extraído")
        
        # 2. RESTAURAR BANCO DE DADOS
        print("💾 Restaurando banco de dados...")
        backup_db = extract_dir / "database.db"
        
        if backup_db.exists():
            db_url = settings.database_url
            if not db_url.startswith("sqlite:///"):
                print("   ⚠️  Banco de dados não é SQLite. Restore manual necessário.")
            else:
                db_path = Path(db_url.replace("sqlite:///", ""))
                
                # Faz backup do banco atual se existir
                if db_path.exists():
                    backup_old = db_path.parent / f"{db_path.stem}_old_{int(Path(backup_db).stat().st_mtime)}.db"
                    shutil.copy2(db_path, backup_old)
                    print(f"   ✅ Backup do banco atual criado: {backup_old.name}")
                
                # Restaura o banco
                shutil.copy2(backup_db, db_path)
                size_mb = db_path.stat().st_size / (1024 * 1024)
                print(f"   ✅ Banco de dados restaurado: {size_mb:.2f} MB")
                
                # Reinicializa o banco
                init_db()
                print("   ✅ Banco de dados inicializado")
        else:
            print("   ⚠️  Arquivo de banco de dados não encontrado no backup")
        
        # 3. RESTAURAR ARQUIVOS DE UPLOAD
        print("📁 Restaurando arquivos de upload...")
        backup_uploads = extract_dir / "uploads"
        
        if backup_uploads.exists():
            upload_dir = settings.upload_dir_path
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Faz backup dos uploads atuais se existirem
            if upload_dir.exists() and any(upload_dir.iterdir()):
                backup_old_uploads = upload_dir.parent / f"uploads_old_{int(Path(backup_uploads).stat().st_mtime)}"
                if backup_old_uploads.exists():
                    shutil.rmtree(backup_old_uploads)
                shutil.copytree(upload_dir, backup_old_uploads)
                print(f"   ✅ Backup dos uploads atuais criado: {backup_old_uploads.name}")
            
            # Remove uploads atuais
            if upload_dir.exists():
                shutil.rmtree(upload_dir)
            
            # Restaura uploads do backup
            shutil.copytree(backup_uploads, upload_dir)
            
            # Conta arquivos
            pdf_count = len(list((upload_dir / "pdfs").glob("*"))) if (upload_dir / "pdfs").exists() else 0
            gif_count = len(list((upload_dir / "gifs").glob("*"))) if (upload_dir / "gifs").exists() else 0
            
            print(f"   ✅ Arquivos restaurados: {pdf_count} PDFs, {gif_count} GIFs")
        else:
            print("   ⚠️  Diretório de uploads não encontrado no backup")
        
        # 4. MOSTRAR INFORMAÇÕES DO BACKUP
        backup_info_file = extract_dir / "backup_info.json"
        if backup_info_file.exists():
            with open(backup_info_file, "r", encoding="utf-8") as f:
                backup_info = json.load(f)
            print()
            print("📋 Informações do backup:")
            print(f"   Data: {backup_info.get('timestamp', 'N/A')}")
            print(f"   Versão: {backup_info.get('app_version', 'N/A')}")
        
        # 5. LIMPAR ARQUIVOS TEMPORÁRIOS
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        
        print()
        print("=" * 60)
        print("✅ RESTORE CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print()
        print("⚠️  IMPORTANTE:")
        print("   1. Verifique se o arquivo .env está configurado corretamente")
        print("   2. Reinicie o servidor para aplicar as mudanças")
        print("   3. Verifique se os arquivos foram restaurados corretamente")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERRO DURANTE RESTORE")
        print("=" * 60)
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Limpa diretório temporário
        extract_dir = Path(__file__).parent.parent / "backups" / "restore_temp"
        if extract_dir.exists():
            try:
                shutil.rmtree(extract_dir)
            except:
                pass

if __name__ == "__main__":
    sys.exit(main())
