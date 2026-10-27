# Milestone lead bot: Windows PC setup, part 1 of 2.
# Right-click PowerShell > "Run as administrator", then:
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\setup-windows.ps1

$ErrorActionPreference = 'Stop'

$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
  [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { Write-Error 'Run this in PowerShell as Administrator.'; exit 1 }

# 1. Identify the machine (replaces msinfo32). Saved to the Desktop to send to Claude.
$cpu   = Get-CimInstance Win32_Processor | Select-Object -First 1
$board = Get-CimInstance Win32_BaseBoard
$os    = Get-CimInstance Win32_OperatingSystem
$gpu   = Get-CimInstance Win32_VideoController | Select-Object -First 1
$info = @"
CPU:            $($cpu.Name) ($($cpu.NumberOfCores) cores / $($cpu.NumberOfLogicalProcessors) threads)
Virtualization: $($cpu.VirtualizationFirmwareEnabled)
Board:          $($board.Manufacturer) $($board.Product)
RAM:            $([math]::Round($os.TotalVisibleMemorySize / 1MB)) GB
GPU:            $($gpu.Name) (driver $($gpu.DriverVersion))
Windows:        $($os.Caption) build $($os.BuildNumber)
Free on C:      $([math]::Round((Get-PSDrive C).Free / 1GB)) GB
"@
$info | Out-File "$env:USERPROFILE\Desktop\pc-info.txt" -Encoding utf8
Write-Host $info
if (-not $cpu.VirtualizationFirmwareEnabled) {
  Write-Warning 'Virtualization looks OFF. If WSL fails after the reboot, turn on VT-x / AMD-V / SVM in the BIOS.'
}

# 2. Apps
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
  Write-Error 'winget is missing. Install "App Installer" from the Microsoft Store, then run this again.'; exit 1
}
$apps = @(
  'Google.Chrome',                  # the bot's browser
  'Tailscale.Tailscale',            # private link to the Mac mini and your phone
  'Ollama.Ollama',                  # small local model on the GTX 1660 (wired up later)
  'Microsoft.Sysinternals.Autologon' # signs in automatically after a restart
)
foreach ($id in $apps) {
  Write-Host "== Installing $id =="
  winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements
}

# 3. Never sleep; drop hibernation (frees ~RAM-sized space on the 128GB SSD)
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change monitor-timeout-ac 10
powercfg /hibernate off

# 4. Give WSL 14 of the 20 GB
@"
[wsl2]
memory=14GB
swap=4GB
"@ | Out-File "$env:USERPROFILE\.wslconfig" -Encoding ascii

# 5. WSL + Ubuntu (needs a restart)
wsl --install -d Ubuntu

Write-Host ''
Write-Host 'Part 1 done. Restart the PC, then follow step 3 in the README (Ubuntu).'
Write-Host "Send Claude the file on your Desktop: pc-info.txt"
