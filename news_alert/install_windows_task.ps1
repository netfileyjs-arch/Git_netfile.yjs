# 매일 아침 9시에 news_alert.py 를 실행하도록 Windows 작업 스케줄러에 등록합니다.
# PC가 9시에 꺼져 있었다면 켜진 직후 한 번 실행됩니다 (StartWhenAvailable).
# 실행: PowerShell 에서  powershell -ExecutionPolicy Bypass -File .\install_windows_task.ps1
# 삭제: Unregister-ScheduledTask -TaskName "NewsKeywordAlert" -Confirm:$false

$TaskName = "NewsKeywordAlert"
$Time = "09:00"
$Script = Join-Path $PSScriptRoot "news_alert.py"

# 콘솔 창이 뜨지 않도록 pythonw 사용
$Pythonw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $Pythonw) {
    Write-Error "pythonw.exe 를 찾을 수 없습니다. Python 설치 시 'Add python.exe to PATH' 를 체크했는지 확인하세요."
    exit 1
}

$Action = New-ScheduledTaskAction -Execute $Pythonw -Argument "`"$Script`"" -WorkingDirectory $PSScriptRoot
$Trigger = New-ScheduledTaskTrigger -Daily -At $Time
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Force | Out-Null
Write-Host "등록 완료: 매일 $Time 에 '$Script' 실행"
