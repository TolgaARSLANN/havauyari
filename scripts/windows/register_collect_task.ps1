<#
HavaUyarı saatlik toplama görevini Windows Görev Zamanlayıcı'ya kaydeder.

Görev her saatin 10. dakikasında WSL'de scripts/collect.sh betiğini çalıştırır. Pencere açmaz
(conhost --headless), yalnızca oturum açıkken çalışır, bilgisayar uykudayken kaçırılan çalışmayı
uyanınca bir kez yapar. Çıktı: <depo>/logs/collect.log

Kaydetmek:   powershell -ExecutionPolicy Bypass -File scripts\windows\register_collect_task.ps1
Kaldırmak:   powershell -ExecutionPolicy Bypass -File scripts\windows\register_collect_task.ps1 -Remove
Elle çalıştırmak:  Start-ScheduledTask -TaskName "HavaUyari Saatlik Toplama"
#>
param(
    [string]$Distro = "Ubuntu-24.04",
    [string]$RepoPath = "~/projects/havauyari",
    [int]$Minute = 10,
    [switch]$Remove
)

$TaskName = "HavaUyari Saatlik Toplama"

if ($Remove) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Görev kaldırıldı: $TaskName"
    return
}

# conhost --headless: her saat siyah bir konsol penceresi açılmasın
$wslArgs = "-d $Distro --cd $RepoPath -- bash scripts/collect.sh"
$action = New-ScheduledTaskAction -Execute "conhost.exe" -Argument "--headless wsl.exe $wslArgs"

$start = (Get-Date).Date.AddHours((Get-Date).Hour + 1).AddMinutes($Minute)
$trigger = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Hours 1)

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal `
    -Description "HavaUyarı: tüm istasyonlar için saatlik PM2.5 tahmini ve ölçümleri PostgreSQL'e kaydeder (WSL: $Distro, $RepoPath)." `
    -Force | Out-Null

$task = Get-ScheduledTask -TaskName $TaskName
Write-Host "Görev kaydedildi: $TaskName"
Write-Host "Durum: $($task.State) · ilk çalışma: $start · her saat"
