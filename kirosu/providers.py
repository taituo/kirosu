from __future__ import annotations
import abc
import logging
import os
import subprocess
from typing import Protocol

class LLMProvider(Protocol):
    def run(self, prompt: str, system_prompt: str | None = None, workdir: str | None = None) -> str:
        ...

class KiroCliProvider:
    def __init__(self, model: str | None = None):
        self.model = model

    def run(self, prompt: str, system_prompt: str | None = None, workdir: str | None = None) -> str:
        cmd = ["kiro-cli", "chat", "--no-interactive", "--wrap", "never"]
        if self.model:
            cmd.extend(["--model", self.model])
            
        cmd.append("--trust-all-tools")
        full_prompt = f"System: {system_prompt}\n\nUser: {prompt}" if system_prompt else prompt
        cmd.append(full_prompt)
        
        env = os.environ.copy()
        process = subprocess.run(
            cmd, capture_output=True, text=True, check=False, env=env, cwd=workdir
        )
        
        if process.returncode != 0:
            msg = (process.stderr or process.stdout or "").strip()
            raise RuntimeError(f"kiro-cli failed: {msg}")
            
        return process.stdout or ""

class CodexProvider:
    def __init__(self, model: str | None = "gpt-5.1-codex-mini"):
        self.model = model

    def run(self, prompt: str, system_prompt: str | None = None, workdir: str | None = None) -> str:
        # User requested specific dangerous flags for speed/automation
        # Syntax: codex exec [OPTIONS] [PROMPT]
        cmd = [
            "codex", 
            "exec",
            "--dangerously-bypass-approvals-and-sandbox",
            "--model", self.model
        ]
        
        # Add extra args (e.g. --search)
        extra_args = os.environ.get("KIRO_CODEX_EXTRA_ARGS")
        if extra_args:
            cmd.extend(extra_args.split())
        
        full_prompt = f"System: {system_prompt}\n\nUser: {prompt}" if system_prompt else prompt
        cmd.append(full_prompt)
        
        env = os.environ.copy()
        process = subprocess.run(
            cmd, capture_output=True, text=True, check=False, env=env, cwd=workdir
        )
        
        if process.returncode != 0:
            msg = (process.stderr or process.stdout or "").strip()
            raise RuntimeError(f"codex failed: {msg}")
            
        return process.stdout or ""

def get_provider(name: str | None = None, model: str | None = None) -> LLMProvider:
    # Default to kiro if not specified
    name = name or os.environ.get("KIRO_PROVIDER", "kiro")
    
    if name == "codex":
        logging.info(f"Using CodexProvider with model {model or 'default'}")
        return CodexProvider(model)
    else:
        return KiroCliProvider(model)
