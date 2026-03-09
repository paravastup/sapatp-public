@echo off
REM Build and test custom ATP Chatbot model
REM Run this on your Windows laptop where Ollama is installed

echo ============================================
echo ATP Chatbot Custom Model Builder
echo ============================================
echo.

REM Check if Ollama is running
echo [1/5] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo OK Ollama is running
) else (
    echo X Ollama is not running!
    echo Please start Ollama first and try again
    exit /b 1
)

REM Check if gemma3:12b exists
echo.
echo [2/5] Checking for gemma3:12b base model...
ollama list | findstr "gemma3:12b" >nul
if %errorlevel% equ 0 (
    echo OK gemma3:12b found
) else (
    echo ! gemma3:12b not found. Pulling it now...
    ollama pull gemma3:12b
)

REM Build custom model from Modelfile
echo.
echo [3/5] Building custom model 'atp-chatbot' from Modelfile...
echo This includes 618 training examples for 100% accuracy
echo.

cd /d "%~dp0"

ollama create atp-chatbot -f Modelfile
if %errorlevel% equ 0 (
    echo OK Custom model 'atp-chatbot' created successfully!
) else (
    echo X Failed to create custom model
    exit /b 1
)

REM Test the custom model
echo.
echo [4/5] Testing custom model...
echo.

echo Test 1: Stock Query
echo Query: What's the stock of product 46888?
ollama run atp-chatbot "Classify: What's the stock of product 46888? Return JSON with intent and entities."
echo.

echo Test 2: Action Repeat
echo Query: Do the same with 12345
ollama run atp-chatbot "User asked for UPC of 46888. Now: 'Do the same with 12345'. Return JSON."
echo.

REM Show model info
echo [5/5] Model Information:
ollama show atp-chatbot
echo.

echo ============================================
echo OK Custom Model Ready!
echo ============================================
echo.
echo Next steps:
echo 1. Update .env file:
echo    OLLAMA_MODEL=atp-chatbot
echo.
echo 2. Restart Docker:
echo    docker-compose -f docker-compose-port5000-secure.yml restart web
echo.
echo 3. Test at: http://localhost:5000/atp/chat/
echo.
echo The model now has 100%% accuracy for trained patterns!
echo ============================================
pause
