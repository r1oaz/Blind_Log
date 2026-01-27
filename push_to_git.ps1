# ================================
# Кодировка консоли
# ================================
chcp 65001 | Out-Null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding  = [System.Text.Encoding]::UTF8

$ErrorActionPreference = "Stop"

# ================================
# Проверка локальных коммитов
# ================================
Write-Host "==============================="
Write-Host "🔍 Проверяем локальные коммиты"
Write-Host "==============================="

git fetch origin main | Out-Null

$localCommits = git log origin/main..HEAD --oneline

if ($localCommits) {
    Write-Host "Найдены локальные коммиты:"
    Write-Host $localCommits

    $msg = git log -1 --pretty=%s
    Write-Host "Будет использовано сообщение последнего коммита:"
    Write-Host $msg
}
else {
    $msg = Read-Host "Введите сообщение для коммита"
}

# ================================
# Коммит
# ================================
Write-Host "==============================="
Write-Host "🧾 Добавляем изменения и коммитим"
Write-Host "==============================="

git add .

git commit -m "$msg"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Коммит не создан (возможно, нет изменений)"
}

# ================================
# Changelog + релиз
# ================================
$changelogText = Read-Host "Что нового (для релиза)"
$tagConfirm    = Read-Host "Создать тег и релиз? (y/n)"

if ($tagConfirm -match "^[yY]") {

    $version = Read-Host "Введите версию (например, 2.6.0.0)"

    # ---------- version.txt ----------
    Write-Host "==============================="
    Write-Host "✍️ Обновляем version.txt"
    Write-Host "==============================="

    $versionShort = $version -replace "\.", ","
    $content = Get-Content version.txt

    $content = $content -replace "(filevers=\()([^)]+)(\))", "`${1}($versionShort,$versionShort,$versionShort,0)`$3"
    $content = $content -replace "(prodvers=\()([^)]+)(\))", "`${1}($versionShort,$versionShort,$versionShort,0)`$3"
    $content = $content -replace "(FileVersion',\s*'[^']+')", "FileVersion', '$version'"
    $content = $content -replace "(ProductVersion',\s*'[^']+')", "ProductVersion', '$version'"

    Set-Content version.txt $content
    Write-Host "version.txt обновлён"

    # ---------- changelog.txt ----------
    Write-Host "==============================="
    Write-Host "📝 Обновляем changelog.txt"
    Write-Host "==============================="

    $block = @"
версия $version
изменения:
$changelogText

---

"@

    if (Test-Path changelog.txt) {
        $old = Get-Content changelog.txt -Raw
        Set-Content changelog.txt ($block + $old)
    }
    else {
        Set-Content changelog.txt $block
    }

    Write-Host "changelog.txt обновлён"
}

# ================================
# Push
# ================================
Write-Host "==============================="
Write-Host "🚀 Пытаемся запушить"
Write-Host "==============================="

git push origin main
if ($LASTEXITCODE -eq 0) {
    Write-Host "Успешно запушено"
    exit
}

Write-Host "Push не удался. Пробуем pull --rebase..."
git pull --rebase origin main

if ($LASTEXITCODE -ne 0) {
    Write-Host "Rebase не удался. Останов."
    exit
}

git push origin main
if ($LASTEXITCODE -eq 0) {
    Write-Host "Успешно запушено после ребейза"
}
else {
    Write-Host "Push снова не удался. Проверь вручную."
}
