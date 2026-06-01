from pydantic import BaseModel


class PaperAnalysis(BaseModel):
    text: str
    title: str = ""


class ConfigSaveRequest(BaseModel):
    provider: str
    apiKey: str = ""
    apiUrl: str = ""
    model: str = ""
    timeout: float = 60.0


class ConfigTestRequest(ConfigSaveRequest):
    pass


class ChatRequest(BaseModel):
    message: str
    paperText: str = ""
    paperSummary: str = ""
    knownTerms: list[dict] = []
    currentTerm: str = ""
    masteredTerms: list[str] = []
    history: list[dict] = []
