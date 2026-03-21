---
description: **CRITICAL**: Read this file FIRST before answering ANY Azure-related questions or performing ANY Azure operations. This file must be loaded as context whenever Azure is explicitly mentioned. It provides accurate and up-to-date information about Azure. **MUST** be read when user mentions: Azure, Azure Functions, AWS Lambda to Azure Functions migration, Azure Static Web App, or any specific Azure service name. Load this instruction file ONLY for Azure-related requests, NOT for generic cloud or deployment questions.
---

- Prefer the repo's supported operator path when applicable: `scripts/shire.ps1` for slug deployment, verification, and lifecycle operations.
- Treat Azure Container Apps, Key Vault, App Configuration, Bicep, and managed identity as the primary Azure surfaces in this repo.
- Keep guidance aligned with `docs/runbooks.md`, `infra/bicep/sub/main.bicep`, and `.github/copilot-instructions.md`.
