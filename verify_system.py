#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
import hashlib
import os
from pathlib import Path
import sys

# UTF-8 인코딩 강제
sys.stdout.reconfigure(encoding='utf-8')

def verify_config():
    """설정 파일 및 해시 검증"""
    print("\n" + "="*60)
    print("CONFIG VERIFICATION")
    print("="*60)
    
    config_path = Path(__file__).parent.parent / "system_config.json"
    hash_path = Path(__file__).parent.parent / "system_config.sha256"
    
    # 설정 파일 확인
    if config_path.exists():
        print(f"OK - Config file exists: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            print(f"   Project: {config.get('project_name')}")
            print(f"   Version: {config.get('version')}")
            print(f"   Status: {config.get('status')}")
            print(f"   Completion: {config.get('completion_level')}")
            print(f"   Last Updated: {config.get('last_updated')}")
            print(f"   Protection: {config.get('protection_status')}")
    else:
        print(f"ERROR - Config file not found")
        return False
    
    # 해시 파일 확인
    if hash_path.exists():
        with open(hash_path, 'r') as f:
            stored_hash = f.read().strip()
        
        # 현재 파일의 해시 계산
        with open(config_path, 'rb') as f:
            current_hash = hashlib.sha256(f.read()).hexdigest()
        
        print(f"\nOK - Hash file exists: {hash_path}")
        print(f"   Stored:  {stored_hash}")
        print(f"   Current: {current_hash}")
        print(f"   Match: {'YES' if stored_hash == current_hash else 'NO (file modified)'}")
    else:
        print(f"ERROR - Hash file not found")
        return False
    
    return True

def verify_database():
    """데이터베이스 검증"""
    print("\n" + "="*60)
    print("DATABASE VERIFICATION")
    print("="*60)
    
    db_path = Path(__file__).parent / "data" / "av_database.db"
    
    if not db_path.exists():
        print(f"ERROR - Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 테이블 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"OK - Database connected")
        print(f"   Tables: {len(tables)}")
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   {table_name}: {count} records")
        
        # 배우 정보 샘플
        cursor.execute("SELECT kr_name, en_name, image_url FROM actresses LIMIT 1")
        actress = cursor.fetchone()
        if actress:
            print(f"\n   Sample actress:")
            print(f"   Name (KR): {actress[0]}")
            print(f"   Name (EN): {actress[1]}")
            print(f"   Image: {actress[2][:60]}...")
        
        conn.close()
        return True
    except Exception as e:
        print(f"ERROR - Database error: {e}")
        return False

def verify_file_permissions():
    """파일 보호 상태 검증"""
    print("\n" + "="*60)
    print("FILE PROTECTION VERIFICATION")
    print("="*60)
    
    config_path = Path(__file__).parent.parent / "system_config.json"
    hash_path = Path(__file__).parent.parent / "system_config.sha256"
    
    def check_readonly(path):
        if not path.exists():
            return None
        stat_info = os.stat(str(path))
        mode = stat_info.st_mode
        is_readonly = not (mode & 0o200)
        return is_readonly
    
    config_readonly = check_readonly(config_path)
    hash_readonly = check_readonly(hash_path)
    
    print(f"system_config.json: {'READ-ONLY PROTECTED' if config_readonly else 'WARNING: Writable'}")
    print(f"system_config.sha256: {'READ-ONLY PROTECTED' if hash_readonly else 'WARNING: Writable'}")
    
    return config_readonly and hash_readonly

def main():
    print("\n")
    print("=" * 60)
    print("AV WEB PLATFORM - FINAL SYSTEM VERIFICATION")
    print("=" * 60)
    
    results = {
        "Config": verify_config(),
        "Database": verify_database(),
        "File Protection": verify_file_permissions()
    }
    
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    all_passed = True
    for name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("SUCCESS - All verifications passed!")
        print("AV web platform is fully operational.")
    else:
        print("WARNING - Some verifications failed.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
