Param(
    [string]$OutputDirectory = "dist",
    [string]$ArchiveName
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
if (-not $ArchiveName -or [string]::IsNullOrWhiteSpace($ArchiveName)) {
    $ArchiveName = "django-maps-release-$timestamp.zip"
}

if (-not (Test-Path $OutputDirectory)) {
    New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
}

$destination = Join-Path $OutputDirectory $ArchiveName

$excludeNames = @(
    ".git", "dist", "logs", "node_modules", "venv", ".venv",
    "__pycache__", "media", "oracleJdk-25"
)
$excludeExtensions = @(".pyc", ".pyo", ".log", ".sqlite3")

$items = Get-ChildItem -Force | Where-Object {
    $name = $_.Name
    ($excludeNames -notcontains $name) -and
    ($excludeExtensions -notcontains $_.Extension)
}

if (-not $items) {
    throw "Nenhum arquivo elegível encontrado para empacotamento."
}

Write-Host "Gerando pacote em $destination ..."
Compress-Archive -Path $items.FullName -DestinationPath $destination -CompressionLevel Optimal -Force

Write-Host "Pacote criado com sucesso:"
Write-Host "  $destination"
Write-Host ""
Write-Host "Lembrete: faça backup do banco (mysqldump) e das variáveis sensíveis (.env, FERNET_KEY) separadamente."
