from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    nickname: str = Field(..., min_length=1)
    agent_file_name: str = Field(..., min_length=1)
