# Günlük tahmin işini Windows Görev Zamanlayıcı'ya kaydeder (Faz 7.3).
# Yönetici yetkisi gerekmez; görev yalnızca oturum açıkken çalışır (parola saklanmaz).
#
#   powershell -ExecutionPolicy Bypass -File scripts\gorev_kur.ps1        # kur / güncelle
#   Unregister-ScheduledTask -TaskName "HavaUyari Gunluk Tahmin"          # kaldır
#
# Tetikleyiciler: her gün 08.17 ve oturum açılışı. Bilgisayar 08.17'de kapalıysa görev
# açılışta telafi edilir (StartWhenAvailable); betik aynı gün ikinci kez çalışmaz.
$ErrorActionPreference = "Stop"

$TaskName = "HavaUyari Gunluk Tahmin"
$Distro = "Ubuntu-24.04"
$Script = "~/projects/havauyari/scripts/gunluk_tahmin.sh"

# conhost --headless: WSL penceresi açılmadan arka planda çalışır
$action = New-ScheduledTaskAction -Execute "conhost.exe" `
    -Argument "--headless wsl.exe -d $Distro -- bash -lc $Script"

$triggers = @(
    (New-ScheduledTaskTrigger -Daily -At "08:17"),
    (New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME")
)

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $triggers `
    -Settings $settings -Principal $principal -Force `
    -Description "HavaUyarı: SİM ölçümleriyle 24 saat sonrası PM2.5 tahmini; sonucu GitHub deposundaki izleme/ klasörüne gönderir." | Out-Null

Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName, State
