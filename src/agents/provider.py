"""Model provider factory — creates the correct LLM client based on configuration."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# Model IDs by role
ORCHESTRATOR_MODEL = "claude-sonnet-4-5-20250929"
PERSONA_MODEL = "claude-haiku-4-5-20251001"

# Bedrock equivalents (for future use)
ORCHESTRATOR_MODEL_BEDROCK = "us.anthropic.claude-sonnet-4-6"
PERSONA_MODEL_BEDROCK = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
BEDROCK_REGION = "us-east-1"


def get_model_id(role: str) -> str:
    """Get the model ID for a given role."""
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    if provider == "bedrock":
        return ORCHESTRATOR_MODEL_BEDROCK if role == "orchestrator" else PERSONA_MODEL_BEDROCK
    return ORCHESTRATOR_MODEL if role == "orchestrator" else PERSONA_MODEL


def get_strands_model(role: str):
    """Create a Strands model provider for the given role."""
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    model_id = get_model_id(role)

    if provider == "bedrock":
        from strands.models.bedrock import BedrockModel
        return BedrockModel(
            model_id=model_id,
            region_name=os.getenv("AWS_REGION", BEDROCK_REGION),
        )
    else:
        from strands.models.anthropic import AnthropicModel
        return AnthropicModel(model_id=model_id)
