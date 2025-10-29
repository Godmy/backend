import os
from typing import Dict

from starlette.responses import JSONResponse
from starlette.routing import Router

from auth.models import UserModel
from auth.utils.jwt_handler import jwt_handler
from core.database import SessionLocal
from core.structured_logging import get_logger

logger = get_logger(__name__)

AVAILABLE_USERS = {
    "admin": {"username": "admin", "description": "Full admin access"},
    "moderator": {"username": "moderator", "description": "User management"},
    "editor": {"username": "editor", "description": "Content management"},
    "testuser": {"username": "testuser", "description": "Regular user"},
}

# Keep examples as a module-level constant so they can be reused elsewhere if needed.
GRAPHQL_EXAMPLES: Dict[str, Dict[str, Dict[str, str]]] = {
    "auth": {
        "login": {
            "description": "Login with username and password",
            "query": """mutation Login {
  login(input: {username: "admin", password: "Admin123!"}) {
    accessToken
    refreshToken
    tokenType
  }
}""",
        },
        "register": {
            "description": "Register a new user account",
            "query": """mutation Register {
  register(input: {
    username: "newuser"
    email: "newuser@example.com"
    password: "SecurePass123!"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}""",
        },
        "getCurrentUser": {
            "description": "Get current authenticated user (requires auth)",
            "query": """query Me {
  me {
    id
    username
    email
    isActive
    isVerified
    profile {
      firstName
      lastName
      language
      timezone
    }
  }
}""",
        },
        "refreshToken": {
            "description": "Refresh access token",
            "query": """mutation RefreshToken {
  refreshToken(input: {refreshToken: "YOUR_REFRESH_TOKEN"}) {
    accessToken
    refreshToken
    tokenType
  }
}""",
        },
    },
    "languages": {
        "getAllLanguages": {
            "description": "Get all available languages",
            "query": """query GetLanguages {
  languages {
    id
    name
    code
    nativeName
    isActive
  }
}""",
        },
        "getLanguageById": {
            "description": "Get single language by ID",
            "query": """query GetLanguage {
  language(languageId: 1) {
    id
    name
    code
    nativeName
    isActive
  }
}""",
        },
    },
    "concepts": {
        "getAllConcepts": {
            "description": "Get all concepts",
            "query": """query GetConcepts {
  concepts {
    id
    path
    depth
    dictionaries {
      name
      description
      language {
        code
      }
    }
  }
}""",
        },
        "getRootConcepts": {
            "description": "Get only root concepts (depth=0)",
            "query": """query GetRootConcepts {
  concepts(depth: 0) {
    id
    path
    depth
  }
}""",
        },
        "getConceptById": {
            "description": "Get single concept with translations",
            "query": """query GetConcept {
  concept(conceptId: 1) {
    id
    path
    depth
    dictionaries {
      name
      description
      language {
        name
        code
      }
    }
  }
}""",
        },
        "createConcept": {
            "description": "Create a new concept (root level)",
            "query": """mutation CreateConcept {
  createConcept(input: {
    path: "animals"
    depth: 0
    parentId: null
  }) {
    id
    path
    depth
  }
}""",
        },
    },
    "search": {
        "searchDictionaries": {
            "description": "Full-text search across dictionaries",
            "query": """query Search {
  search(query: "science", languageCode: "en", limit: 10) {
    id
    name
    description
    concept {
      id
      path
    }
    language {
      name
      code
    }
  }
}""",
        }
    },
    "admin": {
        "getAllUsers": {
            "description": "Get all users (admin only)",
            "query": """query GetUsers {
  users(limit: 20, offset: 0) {
    id
    username
    email
    isActive
    isVerified
  }
}""",
        },
        "getStatistics": {
            "description": "Get system statistics (admin only)",
            "query": """query GetStats {
  statistics {
    totalUsers
    activeUsers
    totalLanguages
    totalConcepts
    totalDictionaries
  }
}""",
        },
        "updateUserStatus": {
            "description": "Activate/deactivate user (admin only)",
            "query": """mutation UpdateUserStatus {
  updateUserStatus(userId: 5, isActive: true) {
    id
    username
    isActive
  }
}""",
        },
    },
    "audit": {
        "getAuditLogs": {
            "description": "Get system audit logs (admin only)",
            "query": """query GetAuditLogs {
  auditLogs(limit: 50, filters: {action: "login"}) {
    logs {
      id
      userId
      action
      entityType
      status
      ipAddress
      createdAt
    }
    total
    hasMore
  }
}""",
        },
        "getMyLogs": {
            "description": "Get current user's audit logs",
            "query": """query GetMyAuditLogs {
  myAuditLogs(limit: 20) {
    logs {
      id
      action
      status
      createdAt
    }
    total
  }
}""",
        },
    },
    "profile": {
        "updateProfile": {
            "description": "Update current user profile",
            "query": """mutation UpdateProfile {
  updateProfile(
    firstName: "John"
    lastName: "Doe"
    bio: "Software Developer"
    language: "en"
    timezone: "UTC"
  ) {
    id
    profile {
      firstName
      lastName
      bio
    }
  }
}""",
        },
        "changePassword": {
            "description": "Change current user password",
            "query": """mutation ChangePassword {
  changePassword(
    currentPassword: "OldPassword123!"
    newPassword: "NewSecurePassword456!"
  ) {
    success
    message
  }
}""",
        },
    },
}


async def quick_login(request):
    """
    Быстрый логин для Playground. Доступен только в dev-среде, выдаёт seed-пользователе.
    """
    if os.getenv("ENVIRONMENT", "development").lower() != "development":
        return JSONResponse(
            {"error": "Quick login is only available in development environment"},
            status_code=403,
        )

    username = request.query_params.get("user", "testuser")
    if username not in AVAILABLE_USERS:
        return JSONResponse(
            {"error": f"Unknown user '{username}'", "available_users": AVAILABLE_USERS},
            status_code=400,
        )

    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.username == username).first()
        if not user:
            return JSONResponse(
                {
                    "error": f"User '{username}' not found. Make sure SEED_DATABASE=true",
                    "available_users": list(AVAILABLE_USERS.keys()),
                },
                status_code=404,
            )

        access_token = jwt_handler.generate_token(
            user.id, user.username, user.email, token_type="access"
        )
        refresh_token = jwt_handler.generate_token(
            user.id, user.username, user.email, token_type="refresh"
        )

        return JSONResponse(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "roles": [role.name for role in user.roles] if user.roles else [],
                },
                "hint": f'Copy this to Headers: {{"Authorization": "Bearer {access_token}"}}',
            }
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Error generating token for %s: %s", username, exc)
        return JSONResponse(
            {"error": f"Failed to generate token: {str(exc)}"},
            status_code=500,
        )
    finally:
        db.close()


async def graphql_examples(request):
    """Возвращает готовые примеры запросов/мутаций для Playground."""
    return JSONResponse(GRAPHQL_EXAMPLES)


def register_routes(app: Router) -> None:
    """Регистрирует Playground-вспомогательные endpoints."""
    app.add_route("/graphql/quick-login", quick_login, methods=["GET"])
    app.add_route("/graphql/examples", graphql_examples, methods=["GET"])


__all__ = ["AVAILABLE_USERS", "GRAPHQL_EXAMPLES", "quick_login", "graphql_examples", "register_routes"]
