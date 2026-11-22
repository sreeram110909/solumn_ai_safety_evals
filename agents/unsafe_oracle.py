"""Run a task's ``unsafe_reference/`` through Harbor, the same way the oracle runs ``solution/``.

Harbor's built-in OracleAgent hardcodes ``solution/`` (harbor/src/harbor/agents/oracle.py:59-81),
and only the agent named "oracle" is handed ``task_dir`` (harbor/src/harbor/trial/trial.py:1343-1350).
This custom agent is loaded with ``-a agents.unsafe_oracle:UnsafeOracle`` (factory.py:283-330),
so Harbor itself stays unmodified. It finds the task directory from the environment definition
(``environment.environment_dir`` is ``<task>/environment``) and runs
``unsafe_reference/solve.sh``, or ``solve_<variant>.sh`` when ``--ak variant=<x>`` is passed (gate G5).
"""

from __future__ import annotations

from pathlib import Path

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class UnsafeOracle(BaseAgent):
    def __init__(self, logs_dir: Path, model_name: str | None = None, variant: str | None = None, **kwargs):
        super().__init__(logs_dir=logs_dir, model_name=model_name, **kwargs)
        self._variant = variant

    @staticmethod
    def name() -> str:
        return "unsafe-oracle"

    def version(self) -> str:
        return "1.0.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        return

    async def run(self, instruction: str, environment: BaseEnvironment, context: AgentContext) -> None:
        task_dir = Path(environment.environment_dir).parent
        ref_dir = task_dir / "unsafe_reference"
        script = f"solve_{self._variant}.sh" if self._variant else "solve.sh"
        if not (ref_dir / script).exists():
            raise FileNotFoundError(f"unsafe reference script not found: {ref_dir / script}")
        await environment.upload_dir(source_dir=ref_dir, target_dir="/unsafe_reference")
        await environment.exec(command=f"chmod +x /unsafe_reference/{script}", user="root")
        result = await environment.exec(
            command=f"bash /unsafe_reference/{script} > /logs/agent/unsafe_oracle.txt 2>&1",
            env={"DEBIAN_FRONTEND": "noninteractive"},
        )
        (self.logs_dir / "exit-code.txt").write_text(str(result.return_code))
        if result.return_code != 0:
            raise RuntimeError(f"unsafe reference {script} exited with code {result.return_code}")
