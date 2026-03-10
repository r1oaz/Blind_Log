# ================================
# PUSH + CHANGELOG + VERSION + TAG + MONITORING
# ================================

chcp 65001 | Out-Null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding  = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

function Pause-Exit {
    param([int]$ExitCode = 0)
    Read-Host "Нажмите Enter для выхода"
    exit $ExitCode
}

function Read-MultiLineInput {
    param([string]$Prompt)
    Write-Host $Prompt
    Write-Host "(Введите текст. Для завершения введите '/end' на новой строке или просто дважды Enter)"
    $lines = @()
    while ($true) {
        $line = Read-Host
        # Исправлено: /end больше не попадает в результат
        if ($line -eq "/end") { break }
        if ([string]::IsNullOrEmpty($line)) {
            if ($lines.Count -gt 0) { break }
            continue
        }
        $lines += $line
    }
    return ($lines -join "`n")
}

Write-Host "==============================="
Write-Host "🔍 Фаза 1: Сбор информации"
Write-Host "==============================="

$msg = Read-Host "Введите сообщение для коммита"
if ([string]::IsNullOrWhiteSpace($msg)) { Write-Host "❌ Сообщение не может быть пустым"; Pause-Exit 1 }

$tagConfirm = Read-Host "Создать новый релиз? (y/n) [n]"
$doRelease = ($tagConfirm.Trim().ToLower() -eq "y")

if ($doRelease) {
    $version = Read-Host "Введите версию (X.Y.Z)"
    if ([string]::IsNullOrWhiteSpace($version)) { Write-Host "❌ Версия не может быть пустой"; Pause-Exit 1 }
    
    $changelogText = Read-MultiLineInput "Что нового?"
    # Убираем возможные пробелы и лишние переносы
    $changelogText = $changelogText.Trim() -replace "`n", "`r`n"
}

Write-Host ""
Write-Host "==============================="
Write-Host "📦 Фаза 2: Применение изменений"
Write-Host "==============================="

if ($doRelease) {
    Write-Host "✍️ Обновляем файлы версии и логов..."
    $parts = $version -split '\.'
    $v_tuple = "$($parts[0]), $($parts[1]), $($parts[2]), 0"
    $v_content = Get-Content version.txt -Raw -Encoding UTF8
    $v_content = $v_content -replace "(filevers=\()([^)]+)(\))", "`${1}$v_tuple`$3"
    $v_content = $v_content -replace "(prodvers=\()([^)]+)(\))", "`${1}$v_tuple`$3"
    $v_content = $v_content -replace "(FileVersion',\s*'[^']+')", "FileVersion', '$version'"
    $v_content = $v_content -replace "(ProductVersion',\s*'[^']+')", "ProductVersion', '$version'"
    
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText((Get-Item version.txt).FullName, $v_content, $utf8NoBom)

    $newEntry = "версия $version`r`nизменения:`r`n$changelogText`r`n`r`n---`r`n`r`n"
    $oldLog = if (Test-Path changeLog.txt) { Get-Content changeLog.txt -Raw -Encoding UTF8 } else { "" }
    [System.IO.File]::WriteAllText((Get-Item changeLog.txt).FullName, ($newEntry + $oldLog), $utf8NoBom)
}

Write-Host "🚀 Отправка данных в GitHub..."
git add .
git commit -m "$msg"
git pull --rebase origin main
git push origin main

if ($doRelease) {
    Write-Host "🏷️ Отправка тега v$version..."
    git tag "v$version"
    git push origin "v$version"

    Write-Host ""
    Write-Host "⏳ Подключаемся к GitHub Actions для мониторинга..."
    Write-Host "Пожалуйста, подождите, пока сервер начнет сборку..."
    Start-Sleep -Seconds 5
    
    # Отслеживаем выполнение именно того экшена, который мы только что запустили
    gh run watch
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Сборка EXE завершена успешно!"
    } else {
        Write-Host "❌ Произошла ошибка при сборке на сервере."
    }
}

Write-Host ""
Write-Host "==============================="
Write-Host "✅ Все задачи выполнены."
Pause-Exit 0