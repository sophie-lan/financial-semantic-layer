"""FastAPI application entry point."""
import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from app.graphql.resolvers import Query

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)

app = FastAPI(title="Financial Semantic Layer")
app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
