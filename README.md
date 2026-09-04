# Model Council

This is a small, offline-first demonstration of a cross-vendor model council.
It sends one request, independently, to one top model from each of three
vendors: Claude, Codex, and Gemini. The first round is blind. In the second
round, each model reads the other two responses without vendor labels and may
revise its positions. The program compares the positions and logs who said
what, including disagreements and minority views.

Why do this? Three different systems can repeat the same weak assumption.
Agreement across vendors is a signal to inspect more closely, not a verdict to
accept automatically. The append-only log is the product: it preserves the
question, each model's reasoning, revisions, disagreements, and the resulting
cut so a person can audit the decision later.

## 30-second offline demo

No vendor CLI, key, package install, or network connection is needed. The three
deterministic fake seats are the default:

```bash
./council-route "Plan a small command-line application" --out /tmp/model-council-public-demo --log /tmp/model-council-public-demo/index.jsonl
```

The command prints a `COUNCIL CUT`, shows all three contributing seats, and
writes the two rounds plus `cut.json` under the selected output directory. It
does not execute the proposed work. To turn an approved cut into ordered work
packages, run:

```bash
./council-delegate /tmp/model-council-public-demo
```

## Delegation pipeline

`delegation/` turns an approved package contract into an implementation attempt
with three distinct responsibilities: an architect defines scope and literal
checks, an implementer changes files in a linked git worktree, and an independent
verifier runs those checks and records `PASS`, `FAIL`, or `BLOCKED` with evidence.
Repeated implementation failures move through bounded implementation tiers;
missing prerequisites do not count as implementation failures, and exhausting
the limits stops the run for an owner decision. Its local fake demonstrates the
entire path without a model or network.

## Connect real model providers

Every seat uses the same function boundary:

```python
run(prompt_file: pathlib.Path, model: str) -> str
```

The provider modules are in `council/lanes/`. To replace a fake, point the
provider at a small script you write that calls your vendor's CLI or SDK, and
name the model it should use:

```bash
export COUNCIL_CLAUDE_COMMAND="/path/to/your/claude-adapter"
export COUNCIL_CLAUDE_MODEL="your-claude-model-id"
export COUNCIL_CODEX_COMMAND="/path/to/your/codex-adapter"
export COUNCIL_CODEX_MODEL="your-codex-model-id"
export COUNCIL_GEMINI_COMMAND="/path/to/your/gemini-adapter"
export COUNCIL_GEMINI_MODEL="your-gemini-model-id"
```

The council appends `--prompt-file PATH --model MODEL` to each command. The
prompt file is JSON with the request, the phase, and, in the revision round,
the other seats' anonymous positions. The adapter should print only the model's
JSON response to stdout and return a nonzero exit code on failure. This keeps
provider authentication and SDK choices outside the council.

## Tests

The normal setup is:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
```

The suite contains 27 pytest tests. One invokes the delegation pipeline's nine
shell checks, so routing, both council rounds, comparison, logging, planning,
contract validation, bounded escalation, worktree isolation, and independent
verification all run offline. The shell checks can also be run directly:

```bash
bash delegation/tests/run.sh
```

Runtime council records go to `.council-runs/` unless `COUNCIL_RUNS` or explicit
`--out` and `--log` paths are supplied. Delegation evidence goes to
`.pipeline-output/` unless `DELEGATION_OUTPUT` is set. Both defaults are ignored
by git.

Copyright (c) 2026 Robert Neal

## About this copy

This is a demonstration copy, published on 2026-09-03 from a private operational
tools suite that the author runs daily. The public copy is complete and runs
offline with deterministic fake seats; it carries its own 27-test suite. The
private suite behind it held 324 offline tests at its 2026-08-18 handoff and
includes the vendor lanes, the delegation planner, and a document scorer that
reused the council's voting reviewers over 536 documents pulled from six external
APIs (125 tests). Those figures describe the private suite, not this copy, and
are the ones cited on the author's resume.
