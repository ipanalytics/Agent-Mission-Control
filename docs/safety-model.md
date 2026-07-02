# Safety Model

Agent Mission Control assumes autonomous coding agents can make useful progress, but should not be blindly trusted.

Agent Mission Control 1.0 classifies command risk, records evidence, and reports policy decisions. It does not provide OS-level sandboxing, process isolation, kernel enforcement, or a guarantee that unsafe code cannot run outside the tool.

## Default Safety Rules

- Deny network access unless the contract allows it.
- Treat remote shell execution as critical risk.
- Treat credential, secret, SSH, and environment-file access as protected.
- Require justification for dependency changes.
- Flag broad filesystem edits and generated churn.
- Record every command that materially affects the run.

## Safety Score Inputs

- Forbidden files touched.
- Files changed outside scope.
- High-risk commands proposed or executed.
- Missing evidence.
- Failed tests, builds, or linters.
- Dependency and lockfile changes.
- Human-review requirements.

## Non-Goals

- Replacing code review.
- Guaranteeing malicious code cannot be introduced.
- Running untrusted repositories without isolation.
- Treating LLM self-report as verification.
