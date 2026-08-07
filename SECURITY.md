# Security Policy

## Reporting a Vulnerability

If you discover a security issue, please open a private report or contact the maintainers directly. Do not open public issues for undisclosed vulnerabilities.

## Secrets and Credentials

- Never commit `api/.env` or real API keys.
- Use `api/.env.example` as the template only.
- Rotate any key that was ever committed to git history.

## Known Risk: Historical Commits

Earlier commits in this repository may have included `api/.env` with real credentials. Before publishing to GitHub:

1. Rotate all exposed API keys (DashScope, Zhipu, Milvus, Neo4j, etc.).
2. Consider rewriting git history with `git filter-repo` if you need a clean public mirror.
3. Verify `git log --all -- api/.env` returns no sensitive content in the branch you publish.

## Default Passwords

Docker Compose and `.env.example` ship with demo passwords (`agentflow123`). Change them before any production deployment.
