from starlette.responses import RedirectResponse
from starlette.routing import Router


async def homepage(request):
    """Редиректит на GraphQL Playground по корневому URL."""
    return RedirectResponse(url="/graphql")


def register_routes(app: Router) -> None:
    app.add_route("/", homepage, methods=["GET"])

