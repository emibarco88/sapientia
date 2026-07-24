from sapientia.config import load_application_environment

load_application_environment()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import router as auth_router
from api.routers.ai_advisor import router as ai_advisor_router
from api.routers.concepts import router as concepts_router
from api.routers.connector_lifecycle import router as connector_lifecycle_router
from api.routers.domains import router as domains_router
from api.routers.enterprise_context import router as enterprise_context_router
from api.routers.enterprise_graph import router as enterprise_graph_router
from api.routers.enterprise_prompt import router as enterprise_prompt_router
from api.routers.explorer import router as explorer_router
from api.routers.intelligence import router as intelligence_router
from api.routers.knowledge_graph import router as knowledge_graph_router
from api.routers.sources import router as sources_router
from api.routers import intelligence_assessments
from api.routers import intelligence_objects
from api.routers import intelligence_evolution
from sapientia.intelligence_experience.api import router as intelligence_experience_router

app = FastAPI(
    title="Sapientia API",
    description="Local MVP API for the Sapientia Enterprise Intelligence Platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.1.111:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(enterprise_prompt_router)
app.include_router(auth_router)
app.include_router(domains_router)
app.include_router(concepts_router)
app.include_router(intelligence_router)
app.include_router(explorer_router)
app.include_router(knowledge_graph_router)
app.include_router(enterprise_graph_router)
app.include_router(ai_advisor_router)
app.include_router(sources_router)
app.include_router(connector_lifecycle_router)
app.include_router(enterprise_context_router)
app.include_router(intelligence_assessments.router)
app.include_router(intelligence_objects.router)
app.include_router(intelligence_evolution.router)
app.include_router(intelligence_experience_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "sapientia-api"}
