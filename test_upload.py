#!/usr/bin/env python3
"""
Тестовый скрипт для проверки File Upload и Audit Logging
"""
import requests
import json
import io
from PIL import Image

BASE_URL = "http://localhost:8000"

def test_login():
    """Тест авторизации"""
    print("1. Testing login...")
    query = """
    mutation Login($username: String!, $password: String!) {
        login(input: {username: $username, password: $password}) {
            accessToken
            refreshToken
            tokenType
        }
    }
    """

    response = requests.post(
        f"{BASE_URL}/graphql",
        json={
            "query": query,
            "variables": {
                "username": "admin",
                "password": "Admin123!"
            }
        }
    )

    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")

    if "data" in data and "login" in data["data"]:
        token = data["data"]["login"]["accessToken"]
        print(f"✓ Login successful! Token: {token[:20]}...")
        return token
    else:
        print("✗ Login failed!")
        return None

def test_audit_logs(token):
    """Тест просмотра audit logs"""
    print("\n2. Testing audit logs query...")
    query = """
    query {
        myAuditLogs(limit: 5) {
            logs {
                id
                action
                status
                description
                createdAt
            }
            total
            hasMore
        }
    }
    """

    response = requests.post(
        f"{BASE_URL}/graphql",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query}
    )

    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")

    if "data" in data and "myAuditLogs" in data["data"]:
        print(f"✓ Found {data['data']['myAuditLogs']['total']} audit logs")
        return True
    else:
        print("✗ Audit logs query failed!")
        return False

def create_test_image():
    """Создает тестовое изображение"""
    img = Image.new('RGB', (500, 500), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def test_file_upload(token):
    """Тест загрузки файла"""
    print("\n3. Testing file upload...")

    # Создаем тестовое изображение
    test_image = create_test_image()

    # GraphQL мутация для загрузки
    operations = {
        "query": """
        mutation UploadFile($file: Upload!) {
            uploadFile(file: $file, fileType: "image") {
                id
                filename
                url
                size
                mimeType
                hasThumbnail
                thumbnailUrl
            }
        }
        """,
        "variables": {"file": None}
    }

    map_data = {
        "0": ["variables.file"]
    }

    files = {
        'operations': (None, json.dumps(operations), 'application/json'),
        'map': (None, json.dumps(map_data), 'application/json'),
        '0': ('test_image.png', test_image, 'image/png')
    }

    response = requests.post(
        f"{BASE_URL}/graphql",
        headers={"Authorization": f"Bearer {token}"},
        files=files
    )

    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")

    if "data" in data and "uploadFile" in data["data"]:
        file_data = data["data"]["uploadFile"]
        print(f"✓ File uploaded successfully!")
        print(f"  - ID: {file_data['id']}")
        print(f"  - URL: {file_data['url']}")
        print(f"  - Has thumbnail: {file_data['hasThumbnail']}")
        return file_data['id']
    else:
        print("✗ File upload failed!")
        return None

def test_my_files(token):
    """Тест получения списка файлов"""
    print("\n4. Testing myFiles query...")
    query = """
    query {
        myFiles(limit: 10) {
            id
            filename
            url
            size
            mimeType
            fileType
            hasThumbnail
            thumbnailUrl
            uploadedAt
        }
    }
    """

    response = requests.post(
        f"{BASE_URL}/graphql",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query}
    )

    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")

    if "data" in data and "myFiles" in data["data"]:
        files = data["data"]["myFiles"]
        print(f"✓ Found {len(files)} files")
        return True
    else:
        print("✗ myFiles query failed!")
        return False

def main():
    """Главная функция"""
    print("=" * 60)
    print("Testing МультиПУЛЬТ File Upload & Audit Logging")
    print("=" * 60)

    # 1. Авторизация
    token = test_login()
    if not token:
        print("\n✗ Cannot continue without authorization")
        return

    # 2. Проверка audit logs
    test_audit_logs(token)

    # 3. Загрузка файла
    file_id = test_file_upload(token)

    # 4. Получение списка файлов
    test_my_files(token)

    print("\n" + "=" * 60)
    print("Testing completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
