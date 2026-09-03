# Delegation pipeline

This pipeline keeps architecture, implementation, and verification as separate
roles. An owner writes a bounded JSON contract. A dispatcher chooses an
implementation tier from recorded attempts. The implementation runs in a
dedicated git worktree. A separate verifier executes only the commands and
thresholds already present in the contract, then records `PASS`, `FAIL`, or
`BLOCKED` with evidence.

`FAIL` consumes an attempt and moves work through the configured implementation
tiers. `BLOCKED` does not consume an implementation attempt; it identifies the
contract or environment owner that must act. When the configured limits are
exhausted, dispatch stops and reports that an owner decision is needed.

The default executor is deterministic and local. It exists to demonstrate the
full control flow without a model or network. Set `DELEGATION_EXECUTOR_COMMAND`
to a command that accepts `CONTRACT WORKTREE EXECUTOR` to connect another
executor. Verification remains a separate process.

Run the shell suite with:

```bash
bash delegation/tests/run.sh
```

The public output directory defaults to `.pipeline-output/` and is ignored by
git. Set `DELEGATION_OUTPUT` to put evidence elsewhere.
