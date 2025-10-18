import strawberry
# Импортируем схемы из модуля languages
from languages.schemas import (
    LanguageQuery, LanguageMutation,
    ConceptQuery, ConceptMutation,
    DictionaryQuery, DictionaryMutation
)
# Импортируем схемы из модуля auth
from auth.schemas import UserQuery, UserMutation, AuthMutation, RoleQuery, RoleMutation
# Импортируем схемы для файлов и аудита
from core.schemas.file import FileQuery, FileMutation
from core.schemas.audit import AuditLogQuery

@strawberry.type
class Query(
    LanguageQuery,
    ConceptQuery,
    DictionaryQuery,
    UserQuery,
    RoleQuery,
    FileQuery,
    AuditLogQuery
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
    FileMutation
):
    pass

schema = strawberry.Schema(Query, Mutation)