from typing import Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from open_notebook.database.repository import ensure_record_id, repo_query
from extensions.outputs.registry import OutputRegistry


class GenerateRequest(BaseModel):
    notebook_id: str
    output_type: str
    language: str = "en"
    model_id: Optional[str] = None


class GenerateResponse(BaseModel):
    content: str
    output_type: str
    language: str


async def get_notebook_context(notebook_id: str) -> str:
    """Gather all source content from a notebook for output generation."""
    sources = await repo_query(
        """
        SELECT in.full_text as text, in.title as title
        FROM reference WHERE out = $notebook_id
        """,
        {"notebook_id": ensure_record_id(notebook_id)},
    )
    if not sources:
        return ""

    parts = []
    for src in sources:
        title = src.get("title", "Untitled")
        text = src.get("text", "")
        if text:
            parts.append(f"### {title}\n{text}")

    return "\n\n---\n\n".join(parts)


async def call_llm(prompt: str, model_id: Optional[str] = None) -> str:
    """Call LLM using open-notebook's existing infrastructure."""
    from esperanto import ai_models

    model = ai_models.get_model(model_id) if model_id else ai_models.get_default_model()
    response = await model.achat([{"role": "user", "content": prompt}])
    return response.text


def create_outputs_router(registry: OutputRegistry) -> APIRouter:
    router = APIRouter()

    @router.get("/types")
    async def list_types():
        return registry.list_all()

    @router.post("/generate", response_model=GenerateResponse)
    async def generate(req: GenerateRequest):
        generator = registry.get(req.output_type)
        if not generator:
            raise HTTPException(
                status_code=404,
                detail=f"Output type '{req.output_type}' not found. Available: {registry.list_types()}",
            )

        context = await get_notebook_context(req.notebook_id)
        if not context:
            raise HTTPException(
                status_code=400,
                detail="Notebook has no sources with content",
            )

        prompt = generator.build_prompt(context=context, language=req.language)
        raw_output = await call_llm(prompt, model_id=req.model_id)
        formatted = generator.format_output(raw_output)

        return GenerateResponse(
            content=formatted,
            output_type=req.output_type,
            language=req.language,
        )

    return router
