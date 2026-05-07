# SOLUCAO DEFINITIVA - Problemas Resolvidos

## 1. Output de comandos perdido no Bash tool

**Problema:** O Bash tool do Claude Code perde output de PowerShell/cmd/Python scripts.

**Causa:** O sandbox do Claude Code nao captura stdout/stderr de subprocessos Windows adequadamente.

**Solucao:** 
- **Metodo principal:** Usar `python -c "..."` com `exec(open('file.py').read())` em vez de `python file.py`
- **Metodo alternativo:** Salvar output em arquivo e ler com `Read` tool
- **Modulo criado:** `shell_exec.py` - executor que SEMPRE salva output em `D:/.openclaude/memory/architect/logs/`

```python
# Forma que FUNCIONA:
python -c "exec(open('D:/.openclaude/skills/memory-architect/script.py').read())"

# Forma que PERDE output:
python D:\.openclaude\skills\memory-architect\script.py
```

## 2. GitHub Push Protection bloqueando tokens

**Problema:** Token GITHUB hardcoded em arquivos eh detectado pelo Push Protection, mesmo em commits antigos.

**Causa:** GitHub escaneia o HISTORICO inteiro do git, nao apenas o commit atual.

**Solucao definitiva:**
1. Remover token de TODOS os arquivos (substituir por `os.environ.get("GITHUB_TOKEN", "")`)
2. Criar fresh repo e fazer force push para sobrescrever historico
3. NUNCA commitar tokens novamente

```bash
# Setup correto:
TOKEN = os.environ.get("GITHUB_TOKEN", "")  # Nunca hardcoded
```

## 3. Git ownership no Windows

**Problema:** `fatal: detected dubious ownership in repository at 'D:/.openclaude/...'`

**Solucao:**
```bash
git config --global --add safe.directory D:/.openclaude
git config --global --add safe.directory D:/.openclaude/saraswat-repo
```

## 4. Git init cria 'master' em vez de 'main'

**Problema:** `git init` cria branch `master` por padrao no Windows.

**Solucao:**
```bash
git init
git branch -M main
```

## 5. Deletar .git corrompido

**Problema:** `shutil.rmtree('.git')` e `rd /s /q .git` falham porque processos git seguram arquivos.

**Solucao:** Em vez de deletar, criar fresh repo em outro local e mover.

## 6. Disco C: abaixo de 1GB

**Solucao aplicada:**
- Removido Python 3.12 antigo (174MB)
- Limpo _cache do Python Local (34MB)
- Limpo Temp directories (1MB+)
- Resultado: 1.12GB livre

## Arquivos no GitHub (limpos, sem tokens)

20 modulos Python + 4 arquivos de memoria + .gitignore
Repositorio: https://github.com/suryamayaharum-droid/saraswat-system

## Lições permanentes

1. **NUNCA** hardcode tokens/secrets em codigo
2. **SEMPRE** salve output de comandos em arquivo
3. **SEMPRE** use `cwd=` parameter em subprocess.run
4. **SEMPRE** renomear branch para `main` apos `git init`
5. **SEMPRE** verifique token em arquivos antes de commitar
