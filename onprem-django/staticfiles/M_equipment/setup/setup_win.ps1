# 관리자 권한 확인 및 요청
# added private ip
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-File", $MyInvocation.MyCommand.Path
    Exit
}

$url = "https://packages.fluentbit.io/windows/fluent-bit-3.0.2-win64.exe"
$output = "C:\Program Files\fluent-bit-3.0.2-win64.exe"
Invoke-WebRequest -Uri $url -OutFile $output
$process = Start-Process -FilePath $output -PassThru
$process.WaitForExit()

$privateIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.AddressState -eq 'Preferred' -and $_.PrefixOrigin -eq 'Dhcp' -and $_.InterfaceAlias -NotLike '*VMware*' -and $_.InterfaceAlias -NotLike '*WSL*'}).IPAddress


$luaScriptContent = @"
function add_private_ip(tag, timestamp, record)
    new_record = record
    new_record["private_ip"] = "$privateIP"
    return 1, timestamp, new_record
end
"@

$luaFilePath = "C:\Program Files\fluent-bit\lua\add_private_ip.lua"
if (-not (Test-Path -Path (Split-Path -Path $luaFilePath -Parent))) {
    New-Item -ItemType Directory -Path (Split-Path -Path $luaFilePath -Parent) | Out-Null
}
Set-Content -Path $luaFilePath -Value $luaScriptContent

$filePath = "C:\Program Files\fluent-bit\conf\fluent-bit.conf"
$newContent = @"
[SERVICE]
    flush        1
    daemon       Off
    log_level    info
    parsers_file parsers.conf
    storage.metrics on

[INPUT]
    Name         winlog
    Channels     Security, Application, System, Windows PowerShell
    Interval_Sec 1
    DB           winlog.sqlite

[FILTER]
    Name          lua
    Match         *
    script        C:\Program Files\fluent-bit\lua\add_private_ip.lua
    call          add_private_ip

[OUTPUT]
    Name         http
    Match        *
    Host         {teiren_server_ip}
    Port         8088
    uri          /collect_log/windows/{tag_name}
    Format       json
"@

Set-Content -Path $filePath -Value $newContent -Force

sc.exe create fluent-bit binpath= '\"C:\Program Files\fluent-bit\bin\fluent-bit.exe\" -c \"C:\Program Files\fluent-bit\conf\fluent-bit.conf\"'
sc.exe start fluent-bit
sc.exe config fluent-bit start=auto