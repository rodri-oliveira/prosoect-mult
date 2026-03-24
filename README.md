# prospect-mult

## Requisitos
- Python 3.11+ instalado e no PATH (Windows).
- PowerShell com permissão para ativar venv (ou usar o Python do venv direto).

## Setup rápido (Windows / PowerShell)
```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## (Opcional) Ativar o venv
Se a ativação estiver bloqueada:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
Depois:
```powershell
.\.venv\Scripts\Activate.ps1
```

## Executar
```powershell
.\.venv\Scripts\python.exe app.py
```
