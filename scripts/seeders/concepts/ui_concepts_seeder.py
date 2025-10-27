"""
Сидер для UI-концептов (интерфейсные переводы)
Зависит от языков
Создает около 200+ концептов с переводами для элементов интерфейса
"""

import logging

from languages.models import ConceptModel, DictionaryModel, LanguageModel
from scripts.seeders.base import BaseSeeder, SeederMetadata, registry

logger = logging.getLogger(__name__)

# Full UI translations dictionary
UI_TRANSLATIONS = {
    # Navigation / Header
    "ui/nav/dashboard": {
        "en": "Dashboard",
        "ru": "Панель управления",
        "es": "Panel de control",
    },
    "ui/nav/concepts": {
        "en": "Concepts",
        "ru": "Концепции",
        "es": "Conceptos",
    },
    "ui/nav/languages": {
        "en": "Languages",
        "ru": "Языки",
        "es": "Idiomas",
    },
    "ui/nav/dictionaries": {
        "en": "Dictionaries",
        "ru": "Словари",
        "es": "Diccionarios",
    },
    "ui/nav/admin": {
        "en": "Admin",
        "ru": "Администрирование",
        "es": "Administración",
    },
    # Buttons
    "ui/button/login": {
        "en": "Login",
        "ru": "Войти",
        "es": "Iniciar sesión",
    },
    "ui/button/logout": {
        "en": "Logout",
        "ru": "Выйти",
        "es": "Cerrar sesión",
    },
    "ui/button/register": {
        "en": "Register",
        "ru": "Регистрация",
        "es": "Registrarse",
    },
    "ui/button/getStarted": {
        "en": "Get Started",
        "ru": "Начать",
        "es": "Comenzar",
    },
    "ui/button/signIn": {
        "en": "Sign in",
        "ru": "Войти",
        "es": "Iniciar sesión",
    },
    "ui/button/save": {
        "en": "Save",
        "ru": "Сохранить",
        "es": "Guardar",
    },
    "ui/button/cancel": {
        "en": "Cancel",
        "ru": "Отмена",
        "es": "Cancelar",
    },
    "ui/button/delete": {
        "en": "Delete",
        "ru": "Удалить",
        "es": "Eliminar",
    },
    "ui/button/edit": {
        "en": "Edit",
        "ru": "Редактировать",
        "es": "Editar",
    },
    "ui/button/create": {
        "en": "Create",
        "ru": "Создать",
        "es": "Crear",
    },
    # Labels
    "ui/label/language": {
        "en": "Language:",
        "ru": "Язык:",
        "es": "Idioma:",
    },
    # Home Page
    "ui/home/title": {
        "en": "Multilingual Content",
        "ru": "Многоязычный контент",
        "es": "Contenido multilingüe",
    },
    "ui/home/subtitle": {
        "en": "Management",
        "ru": "Управление",
        "es": "Gestión",
    },
    "ui/home/description": {
        "en": "Organize concepts, manage dictionaries, and handle multilingual content with ease. Built with GraphQL and modern web technologies.",
        "ru": "Организуйте концепции, управляйте словарями и работайте с многоязычным контентом легко. Создано на GraphQL и современных веб-технологиях.",
        "es": "Organiza conceptos, gestiona diccionarios y maneja contenido multilingüe con facilidad. Construido con GraphQL y tecnologías web modernas.",
    },
    "ui/home/cta/title": {
        "en": "Ready to get started?",
        "ru": "Готовы начать?",
        "es": "¿Listo para comenzar?",
    },
    "ui/home/cta/description": {
        "en": "Join users managing their multilingual content efficiently",
        "ru": "Присоединяйтесь к пользователям, эффективно управляющим многоязычным контентом",
        "es": "Únete a usuarios gestionando su contenido multilingüe eficientemente",
    },
    "ui/home/cta/button": {
        "en": "Create Free Account",
        "ru": "Создать бесплатный аккаунт",
        "es": "Crear cuenta gratuita",
    },
    "ui/home/cta/startTrial": {
        "en": "Start Free Trial",
        "ru": "Начать бесплатный пробный период",
        "es": "Comenzar prueba gratuita",
    },
    "ui/home/feature/concepts/title": {
        "en": "Concept Management",
        "ru": "Управление концепциями",
        "es": "Gestión de conceptos",
    },
    "ui/home/feature/concepts/description": {
        "en": "Organize and structure your content concepts with hierarchical relationships.",
        "ru": "Организуйте и структурируйте концепции контента с иерархическими связями.",
        "es": "Organiza y estructura tus conceptos de contenido con relaciones jerárquicas.",
    },
    "ui/home/feature/multilang/title": {
        "en": "Multi-Language Support",
        "ru": "Поддержка множества языков",
        "es": "Soporte multilingüe",
    },
    "ui/home/feature/multilang/description": {
        "en": "Support unlimited languages and easily manage translations.",
        "ru": "Поддержка неограниченного количества языков и простое управление переводами.",
        "es": "Soporte para idiomas ilimitados y gestión sencilla de traducciones.",
    },
    "ui/home/feature/roles/title": {
        "en": "Role-Based Access",
        "ru": "Ролевой доступ",
        "es": "Acceso basado en roles",
    },
    "ui/home/feature/roles/description": {
        "en": "Control access with fine-grained permissions and role-based authorization.",
        "ru": "Контролируйте доступ с детальными правами и ролевой авторизацией.",
        "es": "Controla el acceso con permisos detallados y autorización basada en roles.",
    },
    "ui/home/footer/copyright": {
        "en": "© 2025 Multipult. All rights reserved.",
        "ru": "© 2025 Мультипульт. Все права защищены.",
        "es": "© 2025 Multipult. Todos los derechos reservados.",
    },
    # Dashboard
    "ui/dashboard/title": {
        "en": "Dashboard",
        "ru": "Панель управления",
        "es": "Panel de control",
    },
    "ui/dashboard/welcome": {
        "en": "Welcome back!",
        "ru": "С возвращением!",
        "es": "¡Bienvenido de nuevo!",
    },
    "ui/dashboard/stats/users": {
        "en": "Total Users",
        "ru": "Всего пользователей",
        "es": "Usuarios totales",
    },
    "ui/dashboard/stats/concepts": {
        "en": "Total Concepts",
        "ru": "Всего концепций",
        "es": "Conceptos totales",
    },
    "ui/dashboard/stats/languages": {
        "en": "Supported Languages",
        "ru": "Поддерживаемые языки",
        "es": "Idiomas soportados",
    },
    # Concepts Page
    "ui/concepts/title": {
        "en": "Concepts",
        "ru": "Концепции",
        "es": "Conceptos",
    },
    "ui/concepts/create": {
        "en": "Create Concept",
        "ru": "Создать концепцию",
        "es": "Crear concepto",
    },
    "ui/concepts/edit": {
        "en": "Edit Concept",
        "ru": "Редактировать концепцию",
        "es": "Editar concepto",
    },
    "ui/concepts/delete": {
        "en": "Delete Concept",
        "ru": "Удалить концепцию",
        "es": "Eliminar concepto",
    },
    "ui/concepts/search": {
        "en": "Search concepts...",
        "ru": "Поиск концепций...",
        "es": "Buscar conceptos...",
    },
    "ui/concepts/filter": {
        "en": "Filter",
        "ru": "Фильтр",
        "es": "Filtrar",
    },
    "ui/concepts/table/name": {
        "en": "Name",
        "ru": "Название",
        "es": "Nombre",
    },
    "ui/concepts/table/language": {
        "en": "Language",
        "ru": "Язык",
        "es": "Idioma",
    },
    "ui/concepts/table/actions": {
        "en": "Actions",
        "ru": "Действия",
        "es": "Acciones",
    },
    "ui/concepts/confirmDelete": {
        "en": "Are you sure you want to delete this concept?",
        "ru": "Вы уверены, что хотите удалить эту концепцию?",
        "es": "¿Está seguro de que desea eliminar este concepto?",
    },
    "ui/concepts/deleteSuccess": {
        "en": "Concept deleted successfully",
        "ru": "Концепция успешно удалена",
        "es": "Concepto eliminado exitosamente",
    },
    "ui/concepts/moveSuccess": {
        "en": "Concept moved successfully",
        "ru": "Концепция успешно перемещена",
        "es": "Concepto movido exitosamente",
    },
    "ui/concepts/updateSuccess": {
        "en": "Concept updated successfully",
        "ru": "Концепция успешно обновлена",
        "es": "Concepto actualizado exitosamente",
    },
    "ui/concepts/createSuccess": {
        "en": "Concept created successfully",
        "ru": "Концепция успешно создана",
        "es": "Concepto creado exitosamente",
    },
    # Languages Page
    "ui/languages/title": {
        "en": "Languages",
        "ru": "Языки",
        "es": "Idiomas",
    },
    "ui/languages/create": {
        "en": "Add Language",
        "ru": "Добавить язык",
        "es": "Agregar idioma",
    },
    "ui/languages/edit": {
        "en": "Edit Language",
        "ru": "Редактировать язык",
        "es": "Editar idioma",
    },
    "ui/languages/table/code": {
        "en": "Code",
        "ru": "Код",
        "es": "Código",
    },
    "ui/languages/table/name": {
        "en": "Name",
        "ru": "Название",
        "es": "Nombre",
    },
    "ui/languages/confirmDelete": {
        "en": "Are you sure you want to delete this language?",
        "ru": "Вы уверены, что хотите удалить этот язык?",
        "es": "¿Está seguro de que desea eliminar este idioma?",
    },
    "ui/languages/deleteSuccess": {
        "en": "Language deleted successfully",
        "ru": "Язык успешно удален",
        "es": "Idioma eliminado exitosamente",
    },
    "ui/languages/updateSuccess": {
        "en": "Language updated successfully",
        "ru": "Язык успешно обновлен",
        "es": "Idioma actualizado exitosamente",
    },
    "ui/languages/createSuccess": {
        "en": "Language created successfully",
        "ru": "Язык успешно создан",
        "es": "Idioma creado exitosamente",
    },
    # Dictionaries Page
    "ui/dictionaries/title": {
        "en": "Dictionaries",
        "ru": "Словари",
        "es": "Diccionarios",
    },
    "ui/dictionaries/search": {
        "en": "Search dictionaries...",
        "ru": "Поиск в словарях...",
        "es": "Buscar diccionarios...",
    },
    "ui/dictionaries/filter": {
        "en": "Filter by language",
        "ru": "Фильтр по языку",
        "es": "Filtrar por idioma",
    },
    "ui/dictionaries/create": {
        "en": "Add Dictionary",
        "ru": "Добавить словарь",
        "es": "Agregar diccionario",
    },
    "ui/dictionaries/confirmDelete": {
        "en": "Are you sure you want to delete this dictionary?",
        "ru": "Вы уверены, что хотите удалить этот словарь?",
        "es": "¿Está seguro de que desea eliminar este diccionario?",
    },
    "ui/dictionaries/deleteSuccess": {
        "en": "Dictionary deleted successfully",
        "ru": "Словарь успешно удален",
        "es": "Diccionario eliminado exitosamente",
    },
    "ui/dictionaries/updateSuccess": {
        "en": "Dictionary updated successfully",
        "ru": "Словарь успешно обновлен",
        "es": "Diccionario actualizado exitosamente",
    },
    "ui/dictionaries/createSuccess": {
        "en": "Dictionary created successfully",
        "ru": "Словарь успешно создан",
        "es": "Diccionario creado exitosamente",
    },
    # Auth Pages
    "ui/auth/login/title": {
        "en": "Sign in to your account",
        "ru": "Войдите в свой аккаунт",
        "es": "Inicia sesión en tu cuenta",
    },
    "ui/auth/login/welcomeBack": {
        "en": "Welcome back",
        "ru": "С возвращением",
        "es": "Bienvenido de nuevo",
    },
    "ui/auth/login/subtitle": {
        "en": "Sign in to your account to continue",
        "ru": "Войдите в свой аккаунт, чтобы продолжить",
        "es": "Inicia sesión en tu cuenta para continuar",
    },
    "ui/auth/usernameOrEmail": {
        "en": "Username or Email",
        "ru": "Имя пользователя или Email",
        "es": "Nombre de usuario o correo",
    },
    "ui/auth/usernamePlaceholder": {
        "en": "Enter your username",
        "ru": "Введите имя пользователя",
        "es": "Ingresa tu nombre de usuario",
    },
    "ui/auth/passwordPlaceholder": {
        "en": "Enter your password",
        "ru": "Введите пароль",
        "es": "Ingresa tu contraseña",
    },
    "ui/auth/rememberMe": {
        "en": "Remember me",
        "ru": "Запомнить меня",
        "es": "Recordarme",
    },
    "ui/auth/forgotPassword": {
        "en": "Forgot password?",
        "ru": "Забыли пароль?",
        "es": "¿Olvidaste tu contraseña?",
    },
    "ui/auth/signingIn": {
        "en": "Signing in...",
        "ru": "Вход...",
        "es": "Iniciando sesión...",
    },
    "ui/auth/orContinueWith": {
        "en": "Or continue with",
        "ru": "Или продолжить с",
        "es": "O continuar con",
    },
    "ui/auth/noAccount": {
        "en": "Don't have an account?",
        "ru": "Нет аккаунта?",
        "es": "¿No tienes una cuenta?",
    },
    "ui/auth/signUpFree": {
        "en": "Sign up for free",
        "ru": "Зарегистрироваться бесплатно",
        "es": "Regístrate gratis",
    },
    "ui/auth/backToLogin": {
        "en": "Back to login",
        "ru": "Вернуться к входу",
        "es": "Volver al inicio de sesión",
    },
    "ui/auth/register/title": {
        "en": "Create your account",
        "ru": "Создайте свой аккаунт",
        "es": "Crea tu cuenta",
    },
    "ui/auth/register/subtitle": {
        "en": "Join us and start managing your content",
        "ru": "Присоединяйтесь к нам и начните управлять контентом",
        "es": "Únete y comienza a gestionar tu contenido",
    },
    "ui/auth/register/usernamePlaceholder": {
        "en": "johndoe",
        "ru": "ivan_petrov",
        "es": "juanperez",
    },
    "ui/auth/register/emailPlaceholder": {
        "en": "john@example.com",
        "ru": "ivan@example.com",
        "es": "juan@ejemplo.com",
    },
    "ui/auth/firstName": {
        "en": "First Name",
        "ru": "Имя",
        "es": "Nombre",
    },
    "ui/auth/lastName": {
        "en": "Last Name",
        "ru": "Фамилия",
        "es": "Apellido",
    },
    "ui/auth/register/firstNamePlaceholder": {
        "en": "John",
        "ru": "Иван",
        "es": "Juan",
    },
    "ui/auth/register/lastNamePlaceholder": {
        "en": "Doe",
        "ru": "Петров",
        "es": "Pérez",
    },
    "ui/auth/register/passwordPlaceholder": {
        "en": "At least 8 characters",
        "ru": "Минимум 8 символов",
        "es": "Al menos 8 caracteres",
    },
    "ui/auth/register/passwordStrengthLabel": {
        "en": "Password strength:",
        "ru": "Надежность пароля:",
        "es": "Seguridad de la contraseña:",
    },
    "ui/auth/register/passwordWeak": {
        "en": "Weak",
        "ru": "Слабый",
        "es": "Débil",
    },
    "ui/auth/register/passwordFair": {
        "en": "Fair",
        "ru": "Средний",
        "es": "Regular",
    },
    "ui/auth/register/passwordGood": {
        "en": "Good",
        "ru": "Хороший",
        "es": "Bueno",
    },
    "ui/auth/register/passwordStrong": {
        "en": "Strong",
        "ru": "Сильный",
        "es": "Fuerte",
    },
    "ui/auth/confirmPassword": {
        "en": "Confirm Password",
        "ru": "Подтвердите пароль",
        "es": "Confirmar contraseña",
    },
    "ui/auth/register/confirmPasswordPlaceholder": {
        "en": "Re-enter your password",
        "ru": "Введите пароль повторно",
        "es": "Vuelve a ingresar tu contraseña",
    },
    "ui/auth/register/passwordMismatch": {
        "en": "Passwords do not match",
        "ru": "Пароли не совпадают",
        "es": "Las contraseñas no coinciden",
    },
    "ui/auth/register/agreeTerms": {
        "en": "Please agree to the Terms and Conditions",
        "ru": "Пожалуйста, примите Условия использования",
        "es": "Por favor acepta los Términos y Condiciones",
    },
    "ui/auth/register/passwordLength": {
        "en": "Password must be at least 8 characters",
        "ru": "Пароль должен содержать минимум 8 символов",
        "es": "La contraseña debe tener al menos 8 caracteres",
    },
    "ui/auth/register/agreePrefix": {
        "en": "I agree to the",
        "ru": "Я принимаю",
        "es": "Acepto los",
    },
    "ui/auth/register/terms": {
        "en": "Terms and Conditions",
        "ru": "Условия использования",
        "es": "Términos y Condiciones",
    },
    "ui/auth/register/and": {
        "en": "and",
        "ru": "и",
        "es": "y",
    },
    "ui/auth/register/privacy": {
        "en": "Privacy Policy",
        "ru": "Политику конфиденциальности",
        "es": "Política de Privacidad",
    },
    "ui/auth/register/creatingAccount": {
        "en": "Creating account...",
        "ru": "Создание аккаунта...",
        "es": "Creando cuenta...",
    },
    "ui/auth/register/haveAccount": {
        "en": "Already have an account?",
        "ru": "Уже есть аккаунт?",
        "es": "¿Ya tienes una cuenta?",
    },
    "ui/auth/register/signInHere": {
        "en": "Sign in here",
        "ru": "Войти здесь",
        "es": "Inicia sesión aquí",
    },
    "ui/auth/forgotPassword/title": {
        "en": "Forgot password?",
        "ru": "Забыли пароль?",
        "es": "¿Olvidaste tu contraseña?",
    },
    "ui/auth/forgotPassword/subtitle": {
        "en": "No worries, we'll send you reset instructions",
        "ru": "Не беспокойтесь, мы отправим вам инструкции",
        "es": "No te preocupes, te enviaremos instrucciones",
    },
    "ui/auth/forgotPassword/emailPlaceholder": {
        "en": "Enter your email",
        "ru": "Введите ваш email",
        "es": "Ingresa tu correo",
    },
    "ui/auth/forgotPassword/sending": {
        "en": "Sending...",
        "ru": "Отправка...",
        "es": "Enviando...",
    },
    "ui/auth/forgotPassword/resetPassword": {
        "en": "Reset password",
        "ru": "Сбросить пароль",
        "es": "Restablecer contraseña",
    },
    "ui/auth/forgotPassword/checkEmail": {
        "en": "Check your email",
        "ru": "Проверьте вашу почту",
        "es": "Revisa tu correo",
    },
    "ui/auth/forgotPassword/sentInstructions": {
        "en": "We've sent password reset instructions to",
        "ru": "Мы отправили инструкции по сбросу пароля на",
        "es": "Hemos enviado instrucciones para restablecer la contraseña a",
    },
    "ui/auth/forgotPassword/step1": {
        "en": "Check your inbox and spam folder",
        "ru": "Проверьте входящие и папку спам",
        "es": "Revisa tu bandeja de entrada y carpeta de spam",
    },
    "ui/auth/forgotPassword/step2": {
        "en": "Click the reset link in the email",
        "ru": "Нажмите на ссылку сброса в письме",
        "es": "Haz clic en el enlace de restablecimiento en el correo",
    },
    "ui/auth/forgotPassword/step3": {
        "en": "Create a new password",
        "ru": "Создайте новый пароль",
        "es": "Crea una nueva contraseña",
    },
    "ui/auth/forgotPassword/noEmail": {
        "en": "Didn't receive the email?",
        "ru": "Не получили письмо?",
        "es": "¿No recibiste el correo?",
    },
    "ui/auth/forgotPassword/tryAgain": {
        "en": "Try again",
        "ru": "Попробовать снова",
        "es": "Intentar de nuevo",
    },
    "ui/auth/email": {
        "en": "Email",
        "ru": "Электронная почта",
        "es": "Correo electrónico",
    },
    "ui/auth/password": {
        "en": "Password",
        "ru": "Пароль",
        "es": "Contraseña",
    },
    "ui/auth/username": {
        "en": "Username",
        "ru": "Имя пользователя",
        "es": "Nombre de usuario",
    },
    # Common
    "ui/common/save": {
        "en": "Save",
        "ru": "Сохранить",
        "es": "Guardar",
    },
    "ui/common/cancel": {
        "en": "Cancel",
        "ru": "Отмена",
        "es": "Cancelar",
    },
    "ui/common/delete": {
        "en": "Delete",
        "ru": "Удалить",
        "es": "Eliminar",
    },
    "ui/common/edit": {
        "en": "Edit",
        "ru": "Редактировать",
        "es": "Editar",
    },
    "ui/common/create": {
        "en": "Create",
        "ru": "Создать",
        "es": "Crear",
    },
    "ui/common/search": {
        "en": "Search",
        "ru": "Поиск",
        "es": "Buscar",
    },
    "ui/common/filter": {
        "en": "Filter",
        "ru": "Фильтр",
        "es": "Filtrar",
    },
    "ui/common/loading": {
        "en": "Loading...",
        "ru": "Загрузка...",
        "es": "Cargando...",
    },
    "ui/common/error": {
        "en": "Error",
        "ru": "Ошибка",
        "es": "Error",
    },
    "ui/common/success": {
        "en": "Success",
        "ru": "Успешно",
        "es": "Éxito",
    },
    "ui/common/noData": {
        "en": "No data available",
        "ru": "Нет данных",
        "es": "No hay datos disponibles",
    },
    "ui/common/back": {
        "en": "Back",
        "ru": "Назад",
        "es": "Atrás",
    },
    "ui/common/allLanguages": {
        "en": "All Languages",
        "ru": "Все языки",
        "es": "Todos los idiomas",
    },
    "ui/common/offline": {
        "en": "You are currently offline. Some features may not be available.",
        "ru": "Вы сейчас офлайн. Некоторые функции могут быть недоступны.",
        "es": "Actualmente estás desconectado. Algunas funciones pueden no estar disponibles.",
    },
}


@registry.register("ui_concepts")
class UIConceptsSeeder(BaseSeeder):
    """Создание UI-концептов для интерфейсных переводов"""

    @property
    def metadata(self) -> SeederMetadata:
        return SeederMetadata(
            name="ui_concepts",
            version="1.0.0",
            description=f"Создание UI-концептов и переводов ({len(UI_TRANSLATIONS)} концептов)",
            dependencies=["languages"],  # Зависит от языков
        )

    def should_run(self) -> bool:
        """Проверить, есть ли уже UI-концепты"""
        return self.db.query(ConceptModel).filter(ConceptModel.path.like("ui/%")).first() is None

    def seed(self) -> None:
        """Создать UI-концепты и переводы с batch оптимизацией"""

        # Получаем языки
        languages = {lang.code: lang for lang in self.db.query(LanguageModel).all()}

        # Проверяем наличие необходимых языков
        required_langs = ["en", "ru", "es"]
        missing_langs = [lang for lang in required_langs if lang not in languages]
        if missing_langs:
            self.logger.warning(
                f"Missing languages: {missing_langs}. Some translations will be skipped."
            )

        # Этап 1: Создаем все концепты по уровням глубины для правильного parent_id
        # Сначала сортируем по глубине (количество / в пути)
        paths_by_depth = {}
        for path in UI_TRANSLATIONS.keys():
            depth = path.count("/")
            if depth not in paths_by_depth:
                paths_by_depth[depth] = []
            paths_by_depth[depth].append(path)

        # Создаем мапинг path -> concept_id
        path_to_id = {}
        total_concepts = 0

        # Создаем концепты уровень за уровнем
        for depth in sorted(paths_by_depth.keys()):
            concepts_data = []

            for path in paths_by_depth[depth]:
                # Находим parent_id
                parent_id = None
                if "/" in path:
                    parent_path = path.rsplit("/", 1)[0]
                    parent_id = path_to_id.get(parent_path)

                concepts_data.append({"path": path, "depth": depth, "parent_id": parent_id})

            # Batch insert концептов этого уровня
            if concepts_data:
                created = self.batch_insert(ConceptModel, concepts_data, batch_size=500)
                self.db.flush()

                # Получаем созданные концепты и строим мапинг
                for concept_data in concepts_data:
                    concept = (
                        self.db.query(ConceptModel)
                        .filter_by(path=concept_data["path"])
                        .first()
                    )
                    if concept:
                        path_to_id[concept.path] = concept.id

                total_concepts += created
                self.logger.info(f"Created {created} concepts at depth {depth}")

        # Commit концептов
        self.db.commit()
        self.metadata.records_created = total_concepts

        # Этап 2: Создаем словарные записи (переводы) с batch insert
        dictionaries_data = []

        for path, translations in UI_TRANSLATIONS.items():
            concept_id = path_to_id.get(path)
            if not concept_id:
                self.logger.warning(f"Concept not found for path: {path}")
                continue

            # Создаем перевод для каждого языка
            for lang_code, translation_text in translations.items():
                if lang_code in languages:
                    dictionaries_data.append(
                        {
                            "concept_id": concept_id,
                            "language_id": languages[lang_code].id,
                            "name": translation_text,
                            "description": f"UI translation for {path}",
                        }
                    )

        # Batch insert словарей
        if dictionaries_data:
            translations_created = self.batch_insert(
                DictionaryModel, dictionaries_data, batch_size=1000
            )
            self.db.commit()
            self.metadata.records_created += translations_created
            self.logger.info(f"Created {translations_created} dictionary translations")

        self.logger.info(
            f"Total: {total_concepts} UI concepts with {translations_created} translations"
        )
