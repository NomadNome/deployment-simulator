"""Sandbox Manager — creates and manages Docker containers for agent isolation."""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field

import requests

from src.models import PersonaType


@dataclass
class SandboxHandle:
    """Reference to a running Docker sandbox."""
    container_id: str
    role: str
    port: int
    endpoint: str

    def url(self, path: str) -> str:
        return f"{self.endpoint}{path}"


class SandboxManager:
    """Manages Docker sandbox lifecycle for agent isolation."""

    IMAGE_NAME = "deployment-sim-agent"

    def __init__(self):
        self.sandboxes: list[SandboxHandle] = []
        self._next_port = 9100
        self._ensure_image()

    def _ensure_image(self):
        """Build the Docker image if it doesn't exist."""
        result = subprocess.run(
            ["docker", "images", "-q", self.IMAGE_NAME],
            capture_output=True, text=True,
        )
        if not result.stdout.strip():
            print(f"Building Docker image: {self.IMAGE_NAME}")
            subprocess.run(
                ["docker", "build", "-t", self.IMAGE_NAME, "-f", "src/sandbox/Dockerfile", "."],
                check=True,
            )

    def create_sandbox(self, role: str) -> SandboxHandle:
        """Create a Docker sandbox for an agent.

        Args:
            role: "orchestrator" or "persona_skeptical_ic", "persona_risk_averse_vp", etc.
        """
        port = self._next_port
        self._next_port += 1

        env_vars = [
            "-e", f"AGENT_ROLE={role}",
            "-e", f"AGENT_PORT=8080",
            "-e", f"ANTHROPIC_API_KEY={os.getenv('ANTHROPIC_API_KEY', '')}",
        ]

        result = subprocess.run(
            ["docker", "run", "-d", "--rm",
             "-p", f"{port}:8080",
             *env_vars,
             self.IMAGE_NAME],
            capture_output=True, text=True, check=True,
        )
        container_id = result.stdout.strip()[:12]

        handle = SandboxHandle(
            container_id=container_id,
            role=role,
            port=port,
            endpoint=f"http://localhost:{port}",
        )
        self.sandboxes.append(handle)

        # Wait for health check
        self._wait_healthy(handle)
        return handle

    def _wait_healthy(self, handle: SandboxHandle, timeout: int = 30):
        """Wait for the sandbox to respond to health checks."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = requests.post(handle.url("/health"), json={}, timeout=2)
                if resp.status_code == 200:
                    return
            except requests.ConnectionError:
                pass
            time.sleep(1)
        raise TimeoutError(f"Sandbox {handle.role} ({handle.container_id}) failed to start")

    def send_request(self, handle: SandboxHandle, path: str, payload: dict) -> dict:
        """Send a request to a sandbox and return the response."""
        resp = requests.post(handle.url(path), json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()

    def destroy_sandbox(self, handle: SandboxHandle):
        """Stop and remove a sandbox container."""
        subprocess.run(["docker", "stop", handle.container_id], capture_output=True)
        self.sandboxes = [s for s in self.sandboxes if s.container_id != handle.container_id]

    def destroy_all(self):
        """Stop all sandbox containers."""
        for handle in list(self.sandboxes):
            self.destroy_sandbox(handle)
