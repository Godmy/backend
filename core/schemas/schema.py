import strawberry

# Импортируем схемы из модуля auth
from auth.schemas import AuthMutation, RoleMutation, RoleQuery, UserMutation, UserQuery
from auth.schemas.admin import AdminMutation, AdminQuery
from core.schemas.audit import AuditLogQuery

# Импортируем схемы для файлов и аудита
from core.schemas.file import FileMutation, FileQuery

# Импортируем схемы для импорта/экспорта
from core.schemas.import_export import ImportExportMutation, ImportExportQuery

# Импортируем схемы для soft delete
from core.schemas.soft_delete import SoftDeleteMutation, SoftDeleteQuery

# Импортируем схемы из модуля languages
from languages.schemas import (
    ConceptMutation,
    ConceptQuery,
    DictionaryMutation,
    DictionaryQuery,
    LanguageMutation,
    LanguageQuery,
    SearchQuery,
)


@strawberry.type
class Query(
    LanguageQuery,
    ConceptQuery,
    DictionaryQuery,
    SearchQuery,
    UserQuery,
    RoleQuery,
    FileQuery,
    AuditLogQuery,
    ImportExportQuery,
    SoftDeleteQuery,
    AdminQuery,
):
    pass


@strawberry.type
class Mutation(
    LanguageMutation,
    ConceptMutation,
    DictionaryMutation,
    UserMutation,
    AuthMutation,
    RoleMutation,
    FileMutation,
    ImportExportMutation,
    SoftDeleteMutation,
    AdminMutation,
):
    pass


schema = strawberry.Schema(Query, Mutation)
