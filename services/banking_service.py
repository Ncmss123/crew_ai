"""CrewAI application service and Groq model configuration."""

from __future__ import annotations

import os
import time
from typing import Any

from crewai import Agent, Crew, LLM, Process, Task
from dotenv import load_dotenv
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from mcp_tools import ACCOUNT_TOOLS, SERVICE_TOOLS, TRANSACTION_TOOLS

load_dotenv()

MODEL_NAME = "groq/openai/gpt-oss-120b"
MAX_RPM = 30
CACHE_BREAKPOINT_KEY = "cache_breakpoint"


class GroqLLM(LLM):
    """Remove CrewAI's internal cache marker before sending messages to Groq."""

    def _prepare_completion_params(
        self,
        messages: str | list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        skip_file_processing: bool = False,
    ) -> dict[str, Any]:
        if isinstance(messages, list):
            messages = [
                {key: value for key, value in message.items() if key != CACHE_BREAKPOINT_KEY}
                for message in messages
            ]
        return super()._prepare_completion_params(messages, tools, skip_file_processing)


def _is_rate_limit_error(error: BaseException) -> bool:
    message = str(error).lower()
    status_code = getattr(error, "status_code", None)
    error_code = str(getattr(error, "code", "")).lower()
    return (
        status_code == 429
        or error_code in {"rate_limit_exceeded", "too_many_requests"}
        or "status code: 429" in message
        or "http 429" in message
    )


@retry(
    retry=retry_if_exception(_is_rate_limit_error),
    wait=wait_exponential(multiplier=1, min=1, max=16),
    stop=stop_after_attempt(3),
    reraise=True,
)
def create_llm() -> GroqLLM:
    """Create CrewAI's native adapter for Groq's openai/gpt-oss-120b model."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Set GROQ_API_KEY before starting the app.")
    return GroqLLM(
        model=MODEL_NAME,
        api_key=api_key,
        max_tokens=1200,
        temperature=0.2,
    )


def _agent(llm: GroqLLM, **kwargs: Any) -> Agent:
    return Agent(llm=llm, max_rpm=MAX_RPM, **kwargs)


def build_crew() -> Crew:
    """Build a hierarchical manager crew with three delegated specialists."""
    llm = create_llm()
    coordinator = _agent(
        llm,
        role="Banking Operations Manager",
        goal="Understand the customer's request and delegate it to the correct specialist.",
        backstory="You coordinate account, transaction, and customer service operations. Never invent data.",
        allow_delegation=True,
        verbose=False,
    )
    accounts_agent = _agent(
        llm,
        role="Account Details Specialist",
        goal="Answer account balance, account type, status, and profile questions accurately.",
        backstory="You access the Accounts MCP Server mock through SQLite tools and cite returned values.",
        tools=ACCOUNT_TOOLS,
        verbose=False,
    )
    transactions_agent = _agent(
        llm,
        role="Transaction and Statement Specialist",
        goal="Provide transaction history and clear spending analysis from the transaction records.",
        backstory="You access the Transactions MCP Server mock through SQLite tools and never guess transactions.",
        tools=TRANSACTION_TOOLS,
        verbose=False,
    )
    service_agent = _agent(
        llm,
        role="Customer Service Specialist",
        goal="Handle address, cheque book, and KYC requests and report request status clearly.",
        backstory="You access the Service MCP Server mock through SQLite tools and confirm created requests.",
        tools=SERVICE_TOOLS,
        verbose=False,
    )
    shared_rules = (
        "The demo customer is user_id USER-1001. Their default account is ACCT-1001. "
        "Use tools for facts, protect privacy by only using those identifiers, and keep the answer concise."
    )
    tasks = [
        Task(
            description=(
                "Delegate the customer request to the appropriate specialist, or multiple specialists when needed. "
                "The customer request is: {user_prompt}\n" + shared_rules
            ),
            expected_output="A direct, helpful response grounded in tool results, with next steps when relevant.",
            agent=accounts_agent,
        ),
        Task(
            description=(
                "Review the request for transaction history, spending, or statement needs and use the available tools. "
                "The customer request is: {user_prompt}\n" + shared_rules
            ),
            expected_output="Accurate transaction or spending findings, or a clear statement that this specialist is not needed.",
            agent=transactions_agent,
        ),
        Task(
            description=(
                "Review the request for service operations such as address change, cheque book, or KYC updates. "
                "Use the service tools when appropriate. The customer request is: {user_prompt}\n" + shared_rules
            ),
            expected_output="A service status or confirmation with a request id when a new request is created.",
            agent=service_agent,
        ),
    ]
    return Crew(
        agents=[accounts_agent, transactions_agent, service_agent],
        tasks=tasks,
        manager_agent=coordinator,
        process=Process.hierarchical,
        max_rpm=MAX_RPM,
        verbose=False,
    )


@retry(
    retry=retry_if_exception(_is_rate_limit_error),
    wait=wait_exponential(multiplier=1, min=1, max=16),
    stop=stop_after_attempt(3),
    reraise=True,
)
def run_banking_crew(user_prompt: str) -> str:
    """Run the banking crew for one user request."""
    if not user_prompt.strip():
        return "Please enter a banking question or service request."
    time.sleep(0.15)
    result = build_crew().kickoff(inputs={"user_prompt": user_prompt.strip()})
    return str(getattr(result, "raw", result))
