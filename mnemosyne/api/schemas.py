from __future__ import annotations

from pydantic import BaseModel, Field


class SubmitRequest(BaseModel):
    problem_id: str
    code: str
    mode: str = "run"  # run = explicit tests


class CheckCodeRequest(BaseModel):
    code: str


class InstallRequirementsRequest(BaseModel):
    scope: str
    problem_id: str | None = None


class AuthorProblemRequest(BaseModel):
    content: str
    overwrite: bool = False


class SaveProblemRequest(BaseModel):
    content: str


class AddTestCaseRequest(BaseModel):
    group: str
    test_case: dict


class AddGeneratedTestCaseRequest(BaseModel):
    group: str
    name: str = "new test"
    args: list


class GenerateExpectedRequest(BaseModel):
    args: list


class AuthorExpectedRequest(BaseModel):
    content: str
    args: list


class LlmProblemDraftRequest(BaseModel):
    request: str
    provider: str | None = None
    api_key: str | None = None
    count: int = 1
    model: str | None = None
    max_attempts: int = 2
    attachments: list[dict] = Field(default_factory=list)
    timeout_seconds: int | None = None


class LlmRepairDraftRequest(BaseModel):
    content: str
    request: str = ""
    provider: str | None = None
    api_key: str | None = None
    model: str | None = None
    max_attempts: int = 2


class LlmProblemEditRequest(BaseModel):
    request: str
    provider: str | None = None
    api_key: str | None = None
    model: str | None = None
    max_attempts: int = 2


class LlmTestDraftRequest(BaseModel):
    request: str
    group: str = "visible_tests"
    count: int = 3
    provider: str | None = None
    api_key: str | None = None
    model: str | None = None


class VerifierValidateRequest(BaseModel):
    content: str
    verify_reference: bool = True


class VerifierRepairHintsRequest(BaseModel):
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ChatGenerateJsonRequest(BaseModel):
    messages: list[dict[str, str]]
    response_schema: dict | None = None
    provider: str | None = None
    api_key: str | None = None
    model: str | None = None
    attachments: list[dict] = Field(default_factory=list)
    timeout_seconds: int | None = None
