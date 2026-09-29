"""Pipeline runs: the run id, the run directory layout, and contract headers.

``saa.contracts.registry`` defines *what* each stage writes; this module decides *where* one run
puts it and fills the machine-written half of every contract. A single ``pipeline_run_id`` ties
the macro view, the 18 asset-class files, the PC proposals, the reviews and the CIO decision
together, and records which dataset versions each of them read.

Layout (docs/contracts.md)::

    runs/<pipeline_run_id>/
      macro/macro-view.json
      cma/<asset_id>/{cma_methods,cma,signals,historical_stats,scenarios,correlation_row}.json
      pc/{covariance.json, pc_research.json, <agent_id>/pc_proposal.json}
      review/{vote_tally.json, <agent_id>/{cro_report,vote}.json,
              <agent_id>/peer_review-<reviewed>.json}
      cio/cio_decision.json
      reports/*.md

Runs live under the git-ignored data directory: they are derived from licensed WRDS data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from saa.config import Config, load_config
from saa.contracts.base import (
    AgentOutput,
    Contract,
    DatasetVersion,
    Header,
    InputRef,
    ModelCall,
    Producer,
)
from saa.contracts.registry import spec
from saa.contracts.registry import write as write_contract
from saa.data.lake import new_run_id

RUNS_DIRNAME = "runs"

# Contracts filed under one agent's own directory; every other contract sits at the top of its
# stage directory. Per-asset contracts are identified by their stage ("cma") instead.
PER_AGENT_CONTRACTS = frozenset({"pc_proposal", "cro_report", "peer_review", "vote"})


@dataclass(frozen=True)
class RunContext:
    """One pipeline run: where its files go, and what every header says."""

    run_id: str
    as_of: date
    root: Path
    ips_version: float
    ips_status: str

    @classmethod
    def create(
        cls,
        config: Config | None = None,
        *,
        as_of: date | str | None = None,
        run_id: str | None = None,
        root: Path | str | None = None,
    ) -> RunContext:
        """Start (or re-open, by passing ``run_id``) a pipeline run."""
        config = config or load_config()
        if as_of is None:
            as_of = date.today()
        elif isinstance(as_of, str):
            as_of = date.fromisoformat(as_of)
        run_id = run_id or new_run_id()
        if root is None:
            root = Path(config.settings.data_dir) / RUNS_DIRNAME / run_id
        return cls(
            run_id=run_id,
            as_of=as_of,
            root=Path(root),
            ips_version=config.ips.version,
            ips_status=config.ips.status,
        )

    # ------------------------------------------------------------------ paths
    def path(
        self,
        contract: str,
        *,
        asset_id: str | None = None,
        agent_id: str | None = None,
        reviewed: str | None = None,
    ) -> Path:
        """Where this run files one contract."""
        entry = spec(contract)
        parts: list[str] = [entry.stage]
        if entry.stage == "cma":
            if not asset_id:
                raise ValueError(f"{contract} is written per asset; pass asset_id")
            parts.append(asset_id)
        elif contract in PER_AGENT_CONTRACTS:
            if not agent_id:
                raise ValueError(f"{contract} is written per agent; pass agent_id")
            parts.append(agent_id)
        filename = entry.filename
        if reviewed is not None:
            if contract != "peer_review":
                raise ValueError("`reviewed` applies only to peer_review")
            filename = f"{Path(filename).stem}-{reviewed}.json"
        return self.root.joinpath(*parts, filename)

    def report_path(self, name: str, *, asset_id: str | None = None) -> Path:
        """Markdown report path. Per-asset reports sit beside that asset's JSON (Exhibit 3)."""
        if asset_id:
            return self.root / "cma" / asset_id / name
        return self.root / "reports" / name

    def relative(self, path: Path | str) -> str:
        """Paths recorded inside a contract are relative to the run directory."""
        return Path(path).resolve().relative_to(self.root.resolve()).as_posix()

    def input_ref(self, contract: str, path: Path | str, sha256: str | None = None) -> InputRef:
        """Reference to an upstream file this agent read, for the run DAG."""
        return InputRef(contract=contract, path=self.relative(path), sha256=sha256)

    # ------------------------------------------------------------------ writing
    def header(
        self,
        contract: str,
        agent: str,
        produced_by: Producer,
        *,
        provenance: dict[str, dict] | None = None,
        inputs: list[InputRef] | None = None,
        report_path: Path | str | None = None,
        model_calls: list[ModelCall] | None = None,
        seed: int | None = None,
    ) -> Header:
        """The machine-written envelope. ``provenance`` takes ``DataStore.provenance()`` as is."""
        return Header(
            contract=contract,
            agent=agent,
            pipeline_run_id=self.run_id,
            as_of=self.as_of,
            generated_at=datetime.now(UTC),
            produced_by=produced_by,
            provenance={
                name: DatasetVersion.model_validate(version)
                for name, version in (provenance or {}).items()
            },
            inputs=list(inputs or []),
            ips_version=self.ips_version,
            ips_status=self.ips_status,
            model_calls=list(model_calls or []),
            seed=seed,
            report_path=self.relative(report_path) if report_path is not None else None,
        )

    def write(
        self,
        contract: str,
        agent: str,
        body: Contract,
        *,
        produced_by: Producer = Producer.SCRIPT,
        asset_id: str | None = None,
        agent_id: str | None = None,
        reviewed: str | None = None,
        provenance: dict[str, dict] | None = None,
        inputs: list[InputRef] | None = None,
        report_path: Path | str | None = None,
        model_calls: list[ModelCall] | None = None,
        seed: int | None = None,
    ) -> Path:
        """Validate ``body`` against its contract, wrap it in a header, and write the file."""
        header = self.header(
            contract,
            agent,
            produced_by,
            provenance=provenance,
            inputs=inputs,
            report_path=report_path,
            model_calls=model_calls,
            seed=seed,
        )
        output: AgentOutput = spec(contract).output_model(header=header, body=body)
        return write_contract(
            output, self.path(contract, asset_id=asset_id, agent_id=agent_id, reviewed=reviewed)
        )

    def write_report(self, text: str, name: str, *, asset_id: str | None = None) -> Path:
        """Write a markdown report (§3.2: narrative alongside every JSON output)."""
        path = self.report_path(name, asset_id=asset_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path
