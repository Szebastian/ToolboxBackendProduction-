@echo off
echo ===================================================
echo     INICIANDO TOOLBOX BACKEND (PYTHON FASTAPI)
echo ===================================================

cd /d "%~dp0"

IF NOT EXIST ".env" (
    echo Creando archivo .env desde .env.example...
    copy .env.example .env
)

IF NOT EXIST "venv" (
    echo Creando entorno virtual de Python...
    python -m venv venv
)

echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo Verificando e instalando dependencias...
pip install -r requirements.txt

echo.
echo ===================================================
echo Servidor iniciando en: http://localhost:10000
echo Swagger Docs en:       http://localhost:10000/docs
echo ===================================================
echo.

uvicorn src.main:app --reload --port 10000 --host 0.0.0.0
pause

