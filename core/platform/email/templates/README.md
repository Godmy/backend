# Email Templates

Эта директория содержит Jinja2 шаблоны для email сообщений.

## 📁 Доступные шаблоны

- `verification.html` - Email верификация при регистрации
- `password_reset.html` - Восстановление пароля

## 🎨 Создание нового шаблона

1. Создайте файл `your_template.html` в этой директории

2. Используйте базовую HTML структуру:

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Заголовок</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }
        .container {
            max-width: 600px;
            margin: 40px auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }
        .content {
            padding: 40px 30px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>МультиПУЛЬТ</h1>
        </div>
        <div class="content">
            <h2>{{ title }}</h2>
            <p>Привет, {{ username }}!</p>
            <!-- Ваш контент здесь -->
        </div>
    </div>
</body>
</html>
```

3. Используйте шаблон в коде:

```python
from core.platform.email.email_service import email_service

html = email_service.render_template(
    "your_template.html",
    title="Заголовок",
    username="john_doe",
    custom_var="значение"
)

email_service.send_email(
    to_email="user@example.com",
    subject="Тема письма",
    html_content=html
)
```

## 🎯 Best Practices

### 1. Inline CSS

Используйте inline стили для лучшей совместимости с почтовыми клиентами:

```html
<p style="color: #555; margin: 20px 0;">Текст</p>
```

### 2. Максимальная ширина 600px

Стандарт для email:

```css
.container {
    max-width: 600px;
    margin: 0 auto;
}
```

### 3. Используйте таблицы для сложной разметки

Для сложных layout используйте `<table>`:

```html
<table width="100%" cellpadding="0" cellspacing="0">
    <tr>
        <td>Контент</td>
    </tr>
</table>
```

### 4. Alt текст для изображений

```html
<img src="logo.png" alt="Логотип МультиПУЛЬТ" />
```

### 5. Fallback для кнопок

```html
<table cellpadding="0" cellspacing="0" border="0">
    <tr>
        <td style="background: #4CAF50; border-radius: 4px;">
            <a href="{{ url }}" style="display: inline-block; padding: 12px 24px; color: white; text-decoration: none;">
                Нажми меня
            </a>
        </td>
    </tr>
</table>
```

### 6. Plain text версия

Всегда предоставляйте текстовую версию:

```python
email_service.send_email(
    to_email="user@example.com",
    subject="Тема",
    html_content=html_content,
    text_content="Текстовая версия"  # ✅
)
```

## 🧪 Тестирование

### Предпросмотр в MailPit

1. Запустите MailPit: `docker-compose -f docker-compose.dev.yml up`
2. Отправьте тестовое письмо
3. Откройте http://localhost:8025
4. Проверьте отображение в различных режимах

### Рендеринг шаблона

```python
from core.platform.email.email_service import email_service

html = email_service.render_template(
    "your_template.html",
    username="test",
    var1="value1"
)

print(html)  # Проверьте результат
```

## 📱 Responsive Design

Используйте media queries для мобильных устройств:

```css
@media only screen and (max-width: 600px) {
    .container {
        width: 100% !important;
    }
    .content {
        padding: 20px !important;
    }
}
```

## 🌐 Локализация

Для поддержки нескольких языков:

```python
# Создайте core/platform/email/templates/ru/verification.html
# Создайте core/platform/email/templates/en/verification.html

# Используйте:
html = email_service.render_template(
    f"{user_locale}/verification.html",
    username=username
)
```

## 🎨 Градиенты для header

```css
/* Фиолетовый */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Розовый */
background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);

/* Синий */
background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);

/* Зеленый */
background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);

/* Оранжевый */
background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
```

## 🔗 Ссылки

- [Email on Acid - CSS Support](https://www.emailonacid.com/blog/article/email-development/which-code-should-i-include-in-every-email/)
- [Can I Email](https://www.caniemail.com/) - Browser support для email
- [HTML Email Boilerplate](https://github.com/seanpowell/Email-Boilerplate)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)

## ⚠️ Что НЕ использовать

- ❌ JavaScript
- ❌ Внешние CSS файлы
- ❌ Видео (используйте GIF или ссылку)
- ❌ Flash
- ❌ Формы (используйте ссылки на веб-форму)
- ❌ Сложные CSS свойства (flexbox, grid)
