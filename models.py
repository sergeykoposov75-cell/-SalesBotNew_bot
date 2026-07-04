from datetime import datetime
from pydantic import BaseModel, model_validator


class ClientData(BaseModel):
    name: str
    phone: str
    email: str
    preferences: str = ""
    timestamp: str = ""

    @model_validator(mode="after")
    def set_timestamp(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        return self


class BotResponse(BaseModel):
    text: str
    from_kb: bool = False
    from_llm: bool = False
    needs_manager: bool = False
