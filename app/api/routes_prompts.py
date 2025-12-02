from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import PromptCreate, PromptRead

router_prompts = APIRouter()

@router_prompts.post("/v1/prompts")
async def create_prompt(prompt: PromptCreate) -> PromptRead:
    new_prompt = PromptRead(
        id="generated_id",
        purpose=prompt.purpose,
        name=prompt.name,
        template=prompt.template,
        version=1,
        active=True
    )
    return new_prompt
