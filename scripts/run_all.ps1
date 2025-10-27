# PowerShell Script Helper - Distributed Synchronization System
# Usage: .\scripts\run_all.ps1 [command]
# Commands: setup, start, test, demo, stop, clean, video-prep

param(
    [Parameter(Mandatory=$false)]
    [string]$Command = "help"
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "🚀 Distributed Synchronization System - Helper Script" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

function Show-Help {
    Write-Host @"

Available Commands:
-------------------
  setup         Install dependencies and setup environment
  start         Start Docker containers
  test          Run automated tests
  demo          Run API demo scenarios
  interactive   Start interactive API client
  benchmark     Run performance benchmarks
  video-prep    Prepare for video recording
  stop          Stop Docker containers
  clean         Clean up everything (containers, volumes, logs)
  help          Show this help message

Examples:
---------
  .\scripts\run_all.ps1 setup
  .\scripts\run_all.ps1 start
  .\scripts\run_all.ps1 test
  .\scripts\run_all.ps1 demo

"@ -ForegroundColor Yellow
}

function Invoke-Setup {
    Write-Host "`n📦 Installing dependencies..." -ForegroundColor Green
    
    # Check if virtual environment exists
    if (-not (Test-Path "$ProjectRoot\venv")) {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        python -m venv "$ProjectRoot\venv"
    }
    
    # Activate virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "$ProjectRoot\venv\Scripts\Activate.ps1"
    
    # Install dependencies
    Write-Host "Installing Python packages..." -ForegroundColor Yellow
    pip install -r "$ProjectRoot\requirements.txt"
    
    # Setup .env if not exists
    if (-not (Test-Path "$ProjectRoot\.env")) {
        Write-Host "Creating .env file..." -ForegroundColor Yellow
        Copy-Item "$ProjectRoot\.env.example" "$ProjectRoot\.env"
    }
    
    Write-Host "`n✅ Setup completed!" -ForegroundColor Green
}

function Invoke-Start {
    Write-Host "`n🐳 Starting Docker containers..." -ForegroundColor Green
    
    Push-Location "$ProjectRoot\docker"
    docker-compose up -d
    Pop-Location
    
    Write-Host "`n⏳ Waiting for containers to be ready (30 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    Write-Host "`n📊 Container Status:" -ForegroundColor Green
    Push-Location "$ProjectRoot\docker"
    docker-compose ps
    Pop-Location
    
    Write-Host "`n✅ Containers started!" -ForegroundColor Green
    Write-Host "Access points:" -ForegroundColor Cyan
    Write-Host "  - Node 1: http://localhost:8001" -ForegroundColor White
    Write-Host "  - Node 2: http://localhost:8002" -ForegroundColor White
    Write-Host "  - Node 3: http://localhost:8003" -ForegroundColor White
    Write-Host "  - Prometheus: http://localhost:9090" -ForegroundColor White
}

function Invoke-Test {
    Write-Host "`n🧪 Running automated tests..." -ForegroundColor Green
    
    & "$ProjectRoot\venv\Scripts\Activate.ps1"
    python "$ProjectRoot\scripts\automated_test.py" --all
    
    Write-Host "`n✅ Testing completed!" -ForegroundColor Green
    Write-Host "Check reports in: $ProjectRoot\reports\" -ForegroundColor Cyan
}

function Invoke-Demo {
    Write-Host "`n🎮 Running API demo scenarios..." -ForegroundColor Green
    
    & "$ProjectRoot\venv\Scripts\Activate.ps1"
    python "$ProjectRoot\scripts\api_client.py" --demo
    
    Write-Host "`n✅ Demo completed!" -ForegroundColor Green
}

function Invoke-Interactive {
    Write-Host "`n🎮 Starting interactive API client..." -ForegroundColor Green
    
    & "$ProjectRoot\venv\Scripts\Activate.ps1"
    python "$ProjectRoot\scripts\api_client.py" --interactive
}

function Invoke-Benchmark {
    Write-Host "`n📈 Running performance benchmarks..." -ForegroundColor Green
    
    & "$ProjectRoot\venv\Scripts\Activate.ps1"
    python "$ProjectRoot\benchmarks\performance_benchmark.py"
    
    Write-Host "`n✅ Benchmarks completed!" -ForegroundColor Green
    Write-Host "Check results in: $ProjectRoot\reports\performance\" -ForegroundColor Cyan
}

function Invoke-VideoPrep {
    Write-Host "`n🎥 Preparing for video recording..." -ForegroundColor Green
    
    # Check Docker status
    Write-Host "`n1. Checking Docker containers..." -ForegroundColor Yellow
    Push-Location "$ProjectRoot\docker"
    docker-compose ps
    Pop-Location
    
    # Test endpoints
    Write-Host "`n2. Testing API endpoints..." -ForegroundColor Yellow
    $urls = @("http://localhost:8001", "http://localhost:8002", "http://localhost:8003")
    foreach ($url in $urls) {
        try {
            $response = Invoke-WebRequest -Uri "$url/health" -TimeoutSec 5 -UseBasicParsing
            Write-Host "  ✅ $url is responsive" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ $url is NOT responsive" -ForegroundColor Red
        }
    }
    
    # Show video script
    Write-Host "`n3. Video presentation script location:" -ForegroundColor Yellow
    Write-Host "  $ProjectRoot\scripts\video_presentation_script.md" -ForegroundColor Cyan
    
    # Show demo data
    Write-Host "`n4. Demo data ready in:" -ForegroundColor Yellow
    Write-Host "  $ProjectRoot\scripts\simple_api_test.py" -ForegroundColor Cyan
    
    Write-Host "`n✅ Video preparation checklist:" -ForegroundColor Green
    Write-Host "  [ ] All containers running" -ForegroundColor White
    Write-Host "  [ ] All endpoints responsive" -ForegroundColor White
    Write-Host "  [ ] Terminal font size 16-18pt" -ForegroundColor White
    Write-Host "  [ ] Close unnecessary applications" -ForegroundColor White
    Write-Host "  [ ] Check microphone audio quality" -ForegroundColor White
    Write-Host "  [ ] Screen recording software ready" -ForegroundColor White
    Write-Host "`nRead: scripts\video_presentation_script.md for full guide" -ForegroundColor Cyan
}

function Invoke-Stop {
    Write-Host "`n🛑 Stopping Docker containers..." -ForegroundColor Yellow
    
    Push-Location "$ProjectRoot\docker"
    docker-compose stop
    Pop-Location
    
    Write-Host "`n✅ Containers stopped!" -ForegroundColor Green
}

function Invoke-Clean {
    Write-Host "`n🧹 Cleaning up..." -ForegroundColor Yellow
    
    $confirm = Read-Host "This will remove containers, volumes, and logs. Continue? (y/N)"
    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        # Stop and remove containers
        Push-Location "$ProjectRoot\docker"
        docker-compose down -v
        Pop-Location
        
        # Clean logs
        if (Test-Path "$ProjectRoot\logs") {
            Remove-Item -Recurse -Force "$ProjectRoot\logs\*"
        }
        
        # Clean reports
        if (Test-Path "$ProjectRoot\reports") {
            Remove-Item -Recurse -Force "$ProjectRoot\reports\*"
        }
        
        Write-Host "`n✅ Cleanup completed!" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Cleanup cancelled" -ForegroundColor Red
    }
}

# Main command dispatcher
switch ($Command.ToLower()) {
    "setup" { Invoke-Setup }
    "start" { Invoke-Start }
    "test" { Invoke-Test }
    "demo" { Invoke-Demo }
    "interactive" { Invoke-Interactive }
    "benchmark" { Invoke-Benchmark }
    "video-prep" { Invoke-VideoPrep }
    "stop" { Invoke-Stop }
    "clean" { Invoke-Clean }
    "help" { Show-Help }
    default { 
        Write-Host "❌ Unknown command: $Command" -ForegroundColor Red
        Show-Help 
    }
}

Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
