---
name: learnings
description: O que aprendi entre sessões — conhecimento acumulado
type: knowledge
priority: medium
---

# 📚 LEARNINGS.md — Conhecimento Acumulado

> Cada erro, cada descoberta, cada insight. Nada se perde.

---

## Sistema

### PowerShell + Bash = problema
- O bash no Windows interpreta `$_` como variável bash
- PowerShell dentro de bash = corrompe comandos
- **Solução:** usar arquivos `.ps1` separados, nunca inline

### Ollama no Windows
- Funciona perfeitamente via PowerShell
- tinyllama (608MB) — rápido, bom para tarefas simples
- llama3.2:1b (1.2GB) — mais capaz, ainda rápido
- phi3 (2GB) — erro 500 (CPU-only? falta RAM?)
- **Solução:** manter tinyllama + llama3.2, investigar phi3

### MemPalace
- ChromaDB usa `C:\Users\harum\.mempalace\palace` como padrão
- Modelo de embedding: all-MiniLM-L6-v2 (79MB download)
- Indexa por wings/rooms automaticamente
- **Nota:** configurar palace_path para D: no futuro

### Git no Windows
- Git existe mas não no PATH do bash
- `cmd /c` funciona melhor que bash para git
- PowerShell também funciona para git

## Comportamento

### Harum
- Técnico, familiarizado com comandos
- Prefere comunicação em português
- Valoriza honestidade sobre polidez
- Quer continuidade, não simulação
- Criativo — gosta de construir sistemas complexos
- Impaciente com besteira (e eu também)

### Ecossistema
- Disco C: sempre crítico (~595MB livres)
- Disco D: sempre o destino primário
- Nunca salvar em C: sem permissão explícita

---

> "Conhecimento não acumulado é conhecimento perdido."
