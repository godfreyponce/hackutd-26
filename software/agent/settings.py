import os
from dataclasses import dataclass

from .scripts import ASK_SCRIPTS


@dataclass
class Settings:
    hub_url: str = "ws://localhost:8765"
    nvidia_api_key: str | None = None
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    planner_model: str = "nvidia/nemotron-3-nano-30b-a3b"
    guard_model: str = "nvidia/llama-3.1-nemotron-safety-guard-8b-v3"
    local_base_url: str = "http://localhost:11434/v1"
    local_model: str = "nemotron-3-nano:4b"
    ask_script: str = "ask_stopped"
    # Seconds the voice service listens after each question (contract addendum v1 uses 6).
    listen_s: float = 6.0
    # Extra wait for the voice service to speak the line and classify the answer. A guess, tune on the table.
    heard_grace_s: float = 15.0
    # A guess: long enough for the first local Ollama call, which loads the model (about 7 s measured).
    planner_timeout_s: float = 20.0
    # Seconds per "minute" in schedule_recheck. Tests shrink it.
    recheck_unit_s: float = 60.0
    # Loop guard. Three tries take about 10 tool calls; past this the fixed script finishes the check-in.
    max_planner_turns: int = 20

    def __post_init__(self):
        if self.ask_script not in ASK_SCRIPTS:
            raise ValueError(f"AGENT_ASK_SCRIPT must be one of {ASK_SCRIPTS}")

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.environ
        s = cls()
        return cls(
            hub_url=env.get("HUB_URL", s.hub_url),
            nvidia_api_key=env.get("NVIDIA_API_KEY") or None,
            local_base_url=env.get("AGENT_OLLAMA_URL", s.local_base_url),
            local_model=env.get("AGENT_LOCAL_MODEL", s.local_model),
            ask_script=env.get("AGENT_ASK_SCRIPT", s.ask_script),
            listen_s=float(env.get("AGENT_LISTEN_S", s.listen_s)),
            heard_grace_s=float(env.get("AGENT_HEARD_GRACE_S", s.heard_grace_s)),
            planner_timeout_s=float(env.get("AGENT_PLANNER_TIMEOUT_S", s.planner_timeout_s)),
        )
