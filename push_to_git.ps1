# ================================
# PUSH + CHANGELOG + VERSION SCRIPT
# ================================
# Логика: сначала все вопросы, потом вся работа (add, commit с version/changelog, push)

# Настройка UTF-8
chcp 65001 | Out-Null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding  = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

# Функция для безопасного чтения многострочного текста
function Read-MultiLineInput {
    param([string]$Prompt)
    Write-Host $Prompt
    Write-Host "(Введите текст. До 5 строк. Пустая строка завершает ввод.)"
    Write-Host "(Если не хотите вводить, просто нажмите Enter сразу)"
    $lines = @()
    $maxLines = 5
    $currentLine = 0
    
    while ($currentLine -lt $maxLines) {
        $line = Read-Host
        if ([string]::IsNullOrEmpty($line)) {
            if ($lines.Count -gt 0) {
                break
            }
            # Если ещё ничего не введено, предложить снова
            continue
        }
        $lines += $line
        $currentLine++
    }
    
    return ($lines -join "`n")
}

# ===================================
# 1. ФАЗА ВОПРОСОВ — сначала всё спрашиваем
# ===================================
Write-Host "==============================="
Write-Host "🔍 Проверяем состояние репозитория"
Write-Host "==============================="

try { & git fetch origin main > $null 2>&1 } catch { }
$localCommits = (git log origin/main..HEAD --oneline 2>$null) -as [string[]]

$msg = ""
if ($localCommits -and $localCommits.Count -gt 0 -and -not [string]::IsNullOrWhiteSpace($localCommits[0])) {
    Write-Host "Найдены локальные коммиты:"
    $localCommits | ForEach-Object { Write-Host $_ }
    $lastMsg = (git log -1 --pretty=%s 2>$null)
    if (-not [string]::IsNullOrWhiteSpace($lastMsg)) {
        Write-Host "Последний коммит: $lastMsg"
        $useLastMsg = Read-Host "Использовать это сообщение? (y/n)"
        if ($useLastMsg.Trim().Length -gt 0 -and $useLastMsg.Trim()[0].ToString().ToLower() -eq "y") {
            $msg = $lastMsg
        }
    }
}

if ([string]::IsNullOrWhiteSpace($msg)) {
    $msg = Read-Host "Введите сообщение для коммита"
}

$msg = $msg.Trim()
if ([string]::IsNullOrWhiteSpace($msg)) {
    Write-Host "❌ Сообщение коммита не может быть пустым"
    exit 1
}

$changelogText = Read-MultiLineInput "Что нового (для релиза)"
$changelogText = $changelogText.Trim()

$tagConfirm = Read-Host "Создать тег и релиз? (y/n)"

$doRelease = $false
$version   = ""

if ($tagConfirm.Trim().Length -gt 0 -and $tagConfirm.Trim()[0].ToString().ToLower() -eq "y") {
    $doRelease = $true
    $version   = Read-Host "Введите версию (например, 2.8.1.0)"
    $version   = $version.Trim()
    if ([string]::IsNullOrWhiteSpace($version)) {
        Write-Host "❌ Версия не может быть пустой"
        exit 1
    }
    
    if ([string]::IsNullOrWhiteSpace($changelogText)) {
        Write-Host "⚠️ Предупреждение: логи изменений пусты, но вы создаёте релиз"
        $confirmEmpty = Read-Host "Продолжить? (y/n)"
        if ($confirmEmpty.Trim().Length -eq 0 -or $confirmEmpty.Trim()[0].ToString().ToLower() -ne "y") {
            Write-Host "❌ Отмена операции"
            exit 1
        }
    }
}

# ===================================
# 2. ФАЗА РАБОТЫ — выполняем всё по порядку
# ===================================
Write-Host ""
Write-Host "==============================="
Write-Host "📦 Выполняем изменения"
Write-Host "==============================="

if ($doRelease) {
    # ---------- version.txt ----------
    Write-Host "✍️ Обновляем version.txt..."
    try {
        $parts = $version -split '\.'
        if ($parts.Count -lt 3) {
            Write-Host "❌ Версия должна быть в формате X.Y.Z или X.Y.Z.W"
            exit 1
        }
        $build = if ($parts.Count -ge 4) { $parts[3] } else { "0" }
        $tuple = "$($parts[0]), $($parts[1]), $($parts[2]), $build"

        $content = Get-Content version.txt -Raw -Encoding UTF8
        $content = $content -replace "(filevers=\()([^)]+)(\))", "`${1}$tuple`$3"
        $content = $content -replace "(prodvers=\()([^)]+)(\))", "`${1}$tuple`$3"
        $content = $content -replace "(FileVersion',\s*'[^']+')", "FileVersion', '$version'"
        $content = $content -replace "(ProductVersion',\s*'[^']+')", "ProductVersion', '$version'"

        Set-Content version.txt $content -Encoding UTF8NoBOM -NoNewline
        Write-Host "   version.txt обновлён"
    }
    catch {
        Write-Host "❌ Ошибка при обновлении version.txt: $_"
        exit 1
    }

    # ---------- changelog.txt ----------
    Write-Host "📝 Обновляем changelog.txt..."
    $block = "версия $version`n"
    $block += "изменения:`n"
    $block += "$changelogText`n"
    $block += "`n---`n`n"
    
    try {
        if (Test-Path changelog.txt) {
            $old = Get-Content changelog.txt -Raw -Encoding UTF8
            Set-Content changelog.txt ($block + $old) -Encoding UTF8NoBOM -NoNewline
        }
        else {
            Set-Content changelog.txt $block -Encoding UTF8NoBOM -NoNewline
        }
        Write-Host "   changelog.txt обновлён"
    }
    catch {
        Write-Host "❌ Ошибка при обновлении changelog.txt: $_"
        exit 1
    }
}

# ---------- git add + commit ----------
Write-Host "🧾 Выполняем git add и коммит..."
try {
    git add . 2>&1 | Out-Null
    git commit -m "$msg" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Коммит создан успешно"
    }
    elseif ($LASTEXITCODE -eq 1) {
        Write-Host "   ⚠️ Коммит не создан (возможно, нет изменений)"
    }
    else {
        Write-Host "   ❌ Ошибка при создании коммита (код: $LASTEXITCODE)"
        exit 1
    }
}
catch {
    Write-Host "   ❌ Критическая ошибка при коммите: $_"
    exit 1
}

# ---------- push ----------
Write-Host ""
Write-Host "🚀 Начинаем пуш в origin main..."

$pushSuccess = $false
$retryCount = 0
$maxRetries = 2

while (-not $pushSuccess -and $retryCount -lt $maxRetries) {
    try {
        git push origin main 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Успешно запушено в origin main"
            $pushSuccess = $true
        }
        else {
            Write-Host "⚠️ Push не удался (код: $LASTEXITCODE). Пробуем pull --rebase..."
            $retryCount++
            
            if ($retryCount -lt $maxRetries) {
                try {
                    git pull --rebase origin main 2>&1 | Out-Null
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "   ✅ Rebase успешен, повторяем push..."
                        continue
                    }
                    else {
                        Write-Host "   ❌ Rebase не удался (код: $LASTEXITCODE)"
                        Write-Host "   Проверьте конфликты вручную и повторите операцию"
                        exit 1
                    }
                }
                catch {
                    Write-Host "   ❌ Ошибка при rebase: $_"
                    exit 1
                }
            }
        }
    }
    catch {
        Write-Host "❌ Критическая ошибка при push: $_"
        exit 1
    }
}

if ($pushSuccess) {
    Write-Host ""
    Write-Host "==============================="
    Write-Host "✅ Все операции завершены успешно!"
    Write-Host "==============================="
    exit 0
}
else {
    Write-Host "❌ Не удалось запушить после нескольких попыток"
    exit 1
}
