#!/usr/bin/env python3
"""
Скрипт для тестирования email сервиса

Использование:
    python scripts/test_email.py
"""

import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.email_service import email_service
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_verification_email():
    """Тест отправки email верификации"""
    logger.info("Testing verification email...")

    result = email_service.send_verification_email(
        to_email="testuser@example.com",
        username="testuser",
        token="test-verification-token-abc123"
    )

    if result:
        logger.info("✅ Verification email sent successfully")
    else:
        logger.error("❌ Failed to send verification email")

    return result


def test_password_reset_email():
    """Тест отправки восстановления пароля"""
    logger.info("Testing password reset email...")

    result = email_service.send_password_reset_email(
        to_email="testuser@example.com",
        username="testuser",
        token="test-reset-token-xyz789"
    )

    if result:
        logger.info("✅ Password reset email sent successfully")
    else:
        logger.error("❌ Failed to send password reset email")

    return result


def test_welcome_email():
    """Тест отправки приветственного письма"""
    logger.info("Testing welcome email...")

    result = email_service.send_welcome_email(
        to_email="newuser@example.com",
        username="newuser"
    )

    if result:
        logger.info("✅ Welcome email sent successfully")
    else:
        logger.error("❌ Failed to send welcome email")

    return result


def test_custom_email():
    """Тест отправки кастомного письма"""
    logger.info("Testing custom email...")

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .button {
                display: inline-block;
                padding: 12px 24px;
                background: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Кастомное письмо</h1>
            <p>Это тестовое письмо с кастомным контентом.</p>
            <a href="https://example.com" class="button">Нажми меня</a>
        </div>
    </body>
    </html>
    """

    text_content = """
    Кастомное письмо

    Это тестовое письмо с кастомным контентом.

    Ссылка: https://example.com
    """

    result = email_service.send_email(
        to_email="custom@example.com",
        subject="Тестовое кастомное письмо",
        html_content=html_content,
        text_content=text_content
    )

    if result:
        logger.info("✅ Custom email sent successfully")
    else:
        logger.error("❌ Failed to send custom email")

    return result


def test_multiple_recipients():
    """Тест отправки нескольким получателям"""
    logger.info("Testing multiple recipients email...")

    result = email_service.send_email(
        to_email=["user1@example.com", "user2@example.com", "user3@example.com"],
        subject="Тест множественной отправки",
        html_content="<h1>Привет!</h1><p>Это письмо отправлено нескольким получателям.</p>",
        text_content="Привет!\n\nЭто письмо отправлено нескольким получателям."
    )

    if result:
        logger.info("✅ Multiple recipients email sent successfully")
    else:
        logger.error("❌ Failed to send email to multiple recipients")

    return result


def main():
    """Запуск всех тестов"""
    logger.info("=" * 60)
    logger.info("Starting Email Service Tests")
    logger.info("=" * 60)

    # Проверка конфигурации
    logger.info(f"\nConfiguration:")
    logger.info(f"  SMTP Host: {email_service.smtp_host}")
    logger.info(f"  SMTP Port: {email_service.smtp_port}")
    logger.info(f"  From Email: {email_service.from_email}")
    logger.info(f"  Use TLS: {email_service.use_tls}")
    logger.info(f"  Frontend URL: {email_service.frontend_url}")

    # Запуск тестов
    tests = [
        ("Verification Email", test_verification_email),
        ("Password Reset Email", test_password_reset_email),
        ("Welcome Email", test_welcome_email),
        ("Custom Email", test_custom_email),
        ("Multiple Recipients", test_multiple_recipients),
    ]

    results = []
    logger.info("\n" + "=" * 60)
    logger.info("Running Tests")
    logger.info("=" * 60 + "\n")

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

        logger.info("")  # Пустая строка между тестами

    # Итоги
    logger.info("=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status}: {test_name}")

    logger.info("")
    logger.info(f"Total: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed!")
        logger.info("\n📧 Check MailPit web UI at: http://localhost:8025")
    else:
        logger.warning(f"⚠️  {total - passed} test(s) failed")

    logger.info("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
