# ================================
# Настройки
# ================================
$ErrorActionPreference = "Stop"

Write-Host "==============================="
Write-Host "🔍 Проверяем локальные коммиты"
Write-Host "==============================="

git fetch origin main | Out-Null

$localCommits = git log origin/main..HEAD --oneline

if ($localCommits) {
    Write-Host "Найдены локальные коммиты:"
    Write-Host $localCommits

    # Берём сообщение последнего коммита
    $msg = git log -1 --pretty=%s
    Write-Host "Будет использовано сообщение:"
    Write-Host $msg
}
else {
    $msg = Read-Host "Введите сообщение для коммита"
}

Write-Host "==============================="
Write-Host "🧾 Добавляем изменения и коммитим"
Write-Host "==============================="

git add .

git commit -m "$msg"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Коммит не создан (возможно, нет изменений)"
}

$changelog = Read-Host "Что нового (для релиза)"
$tagConfirm = Read-Host "Создать тег и релиз? (y/n)"

if ($tagConfirm -match "^[yY]") {

    $version = Read-Host "Введите версию (например, 2.4.0.0)"

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
}

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
