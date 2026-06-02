from pydantic import BaseModel, Field


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
    knownTerms: list[dict] = Field(default_factory=list)
    currentTerm: str = ""
    masteredTerms: list[str] = Field(default_factory=list)
    history: list[dict] = Field(default_factory=list)
    evidenceSnippets: list[dict] = Field(default_factory=list)
    localOnly: bool = False


class LearningSessionRequest(BaseModel):
    title: str = ""
    source: str = "text"
    paperText: str = ""
    paperSummary: str = ""
    knownTerms: list[dict] = Field(default_factory=list)
    analysis: dict = Field(default_factory=dict)


class MasteryUpdateRequest(BaseModel):
    term: str
    mastered: bool = True


class EvidenceRequest(BaseModel):
    question: str = ""
    paperText: str = ""
    knownTerms: list[dict] = Field(default_factory=list)


class PaperLoadRequest(BaseModel):
    title: str = ""
    url: str = ""
    openAccessUrl: str = ""
    pdfUrl: str = ""
    abstract: str = ""
    shortDesc: str = ""


class IntegrationInboundRequest(BaseModel):
    channel: str = "local"
    text: str = ""
    sender: str = ""
    token: str = ""
    metadata: dict = Field(default_factory=dict)


class IntegrationSendRequest(BaseModel):
    channel: str = "wechat"
    text: str = ""
    markdown: bool = False
    token: str = ""
