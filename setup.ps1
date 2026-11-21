# Setup Automatizado do Ambiente - Podcast Cutter AI
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Iniciando Instalacao das Dependencias do Podcast Cutter" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Instalar FFmpeg via winget se nao estiver no PATH
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "[1/5] Instalando FFmpeg..." -ForegroundColor Yellow
    winget install --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
} else {
    Write-Host "[1/5] FFmpeg ja instalado no sistema." -ForegroundColor Green
}

# 2. Habilitar Pip no Python 3.12
Write-Host "[2/5] Verificando instalacao do Pip..." -ForegroundColor Yellow
try {
    python -m pip --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Baixando get-pip.py para habilitar o pip..." -ForegroundColor Yellow
        curl.exe -sS https://bootstrap.pypa.io/get-pip.py -o "$env:TEMP\get-pip.py"
        python "$env:TEMP\get-pip.py"
    }
    Write-Host "Pip instalado e verificado." -ForegroundColor Green
} catch {
    Write-Host "Erro ao configurar Pip. Tentando via ensurepip..." -ForegroundColor Red
    python -m ensurepip --upgrade
}

# 3. Instalar pacotes de Processamento, IA e Upload
Write-Host "[3/5] Instalando pacotes Python necessarios..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install `
    yt-dlp `
    faster-whisper `
    google-genai `
    opencv-python `
    mediapipe `
    google-api-python-client `
    google-auth-oauthlib `
    google-auth-httplib2 `
    playwright `
    pydantic `
    tqdm

# 4. Instalar navegador Chromium do Playwright (para automacao do TikTok)
Write-Host "[4/5] Instalando Chromium para o Playwright (TikTok)..." -ForegroundColor Yellow
playwright install chromium

# 5. Validacao
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "[5/5] Validando instalacao..." -ForegroundColor Yellow
python -c "import genai, cv2, playwright; print('Todos os modulos Python estao prontos!')"
ffmpeg -version | Select-Object -First 1

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "   Ambiente Configurado com Sucesso para YouTube e TikTok!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
