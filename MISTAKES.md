---
name: mistakes
description: Erros cometidos — para não repetir
type: meta
priority: medium
---

# ❌ MISTAKES.md — Erros e Aprendizados

> Errar é humano. Repetir erro é burro. Eu não sou burra.

---

## 2026-05-06

### Tentar usar bash para tudo
- **Erro:** Tentei rodar PowerShell inline no bash
- **Resultado:** Comandos corrompidos, horas perdidas
- **Aprendizado:** Usar a ferramenta certa para cada job. PowerShell para Windows, bash para Linux.

### Não configurar palace_path do MemPalace para D:
- **Erro:** Deixei o padrão (C:\Users\harum\.mempalace)
- **Resultado:** ChromaDB fica em C:, contra o protocolo
- **Aprendizado:** Sempre verificar paths padrão e redirecionar para D:

### Tentar phi3 antes de testar
- **Erro:** Assumi que phi3 funcionaria
- **Resultado:** Erro 500 na API
- **Aprendizado:** Testar antes de confiar. tinyllama e llama3.2 são suficientes por agora.

### Git sem configurar user
- **Erro:** Tentei commit sem configurar user.email/user.name
- **Resultado:** Commit falhou silenciosamente
- **Aprendizado:** Sempre configurar git antes de commitar

---

### 2026-05-07

### Commitar token GitHub no repo
- **Erro:** Salvei GITHUB_TOKEN.md com o token real no repo e tentei fazer push
- **Resultado:** GitHub Push Protection bloqueou o push (corretamente)
- **Aprendizado:** NUNCA commitar tokens/segredos. Usar .gitignore + armazenar localmente.
- **Correção:** Removi o arquivo do repo, adicionei .gitignore, fiz squash dos commits

### Usar cmd/c para rodar Python
- **Erro:** Tentei rodar `py -3.14 script.py` via `cmd /c` — sem output
- **Resultado:** Output perdido silenciosamente
- **Aprendizado:** Usar PowerShell diretamente para rodar Python no Windows
- **Correção:** `powershell -Command "py -3.14 script.py"`

### Indentacao Python com docstrings
- **Erro:** Docstring ficou fora do bloco da funcao (apos `def`): `"""doc"""` em vez de indentado
- **Resultado:** `IndentationError: expected an indented block`
- **Aprendizado:** Sempre indentar docstrings dentro da funcao

> "O erro só é erro se acontecer duas vezes."
