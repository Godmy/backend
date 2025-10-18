import strawberry
from typing import Optional, List


@strawberry.type
class Language:
    """GraphQL тип для языка"""
    id: int
    code: str
    name: str


@strawberry.input
class LanguageInput:
    """Входные данные для создания языка"""
    code: str
    name: str


@strawberry.input
class LanguageUpdateInput:
    """Входные данные для обновления языка"""
    code: Optional[str] = None
    name: Optional[str] = None


@strawberry.type
class LanguageQuery:
    """GraphQL запросы для языков"""
    
    @strawberry.field
    def languages(self) -> List[Language]:
        """Получить список всех языков"""
        from languages.services.language_service import LanguageService
        from core.database import get_db
        
        db = next(get_db())
        service = LanguageService(db)
        languages = service.get_all()
        
        return [Language(
            id=lang.id,
            code=lang.code,
            name=lang.name
        ) for lang in languages]
    
    @strawberry.field
    def language(self, language_id: int) -> Optional[Language]:
        """Получить язык по ID"""
        from languages.services.language_service import LanguageService
        from core.database import get_db
        
        db = next(get_db())
        service = LanguageService(db)
        lang = service.get_by_id(language_id)
        
        if not lang:
            return None
            
        return Language(
            id=lang.id,
            code=lang.code,
            name=lang.name
        )


@strawberry.type
class LanguageMutation:
    """GraphQL мутации для языков"""
    
    @strawberry.mutation
    def create_language(self, input: LanguageInput) -> Language:
        """Создать новый язык"""
        from languages.services.language_service import LanguageService
        from core.database import get_db
        
        db = next(get_db())
        service = LanguageService(db)
        language = service.create(code=input.code, name=input.name)
        
        return Language(
            id=language.id,
            code=language.code,
            name=language.name
        )
    
    @strawberry.mutation
    def update_language(self, language_id: int, input: LanguageUpdateInput) -> Language:
        """Обновить язык"""
        from languages.services.language_service import LanguageService
        from core.database import get_db
        
        db = next(get_db())
        service = LanguageService(db)
        language = service.update(language_id, code=input.code, name=input.name)
        
        if not language:
            raise Exception("Language not found")
        
        return Language(
            id=language.id,
            code=language.code,
            name=language.name
        )
    
    @strawberry.mutation
    def delete_language(self, language_id: int) -> bool:
        """Удалить язык"""
        from languages.services.language_service import LanguageService
        from core.database import get_db
        
        db = next(get_db())
        service = LanguageService(db)
        return service.delete(language_id)
