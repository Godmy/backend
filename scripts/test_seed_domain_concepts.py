#!/usr/bin/env python3
"""
Тестовый скрипт для проверки корректности импорта скрипта инициализации доменных данных
"""

import sys
import os

# Добавляем путь к директории скриптов
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
sys.path.insert(0, backend_dir)

def test_import():
    """Проверка импорта скрипта инициализации"""
    try:
        # Попытка импортировать скрипт
        from scripts.seed_domain_concepts import seed_domain_concepts
        print("✓ SUCCESS: Script imported successfully")
        return True
    except ImportError as e:
        print(f"✗ ERROR: Failed to import script: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: Unexpected error during import: {e}")
        return False

def test_functions_exist():
    """Проверка наличия основных функций"""
    try:
        from scripts.seed_domain_concepts import (
            load_domain_data,
            flatten_hierarchy,
            get_or_create_concept,
            create_dictionary_entries,
            seed_domain_concepts
        )
        
        # Проверяем, что функции существуют (не вызываем их)
        functions = [
            load_domain_data,
            flatten_hierarchy,
            get_or_create_concept,
            create_dictionary_entries,
            seed_domain_concepts
        ]
        
        for func in functions:
            if not callable(func):
                print(f"✗ ERROR: {func.__name__} is not callable")
                return False
                
        print("✓ SUCCESS: All required functions exist and are callable")
        return True
    except ImportError as e:
        print(f"✗ ERROR: Failed to import required functions: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: Unexpected error during function check: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("Testing domain concepts seeding script...")
    print("=" * 50)
    
    # Тест 1: Проверка импорта
    if not test_import():
        return False
        
    # Тест 2: Проверка функций
    if not test_functions_exist():
        return False
        
    print("=" * 50)
    print("✓ ALL TESTS PASSED: Script is ready for use")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)