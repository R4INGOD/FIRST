# Windows PC: 24/7 lead bot setup

The Windows desktop (GTX 1660 6GB, 20GB RAM) becomes the always-on home of the
$15K+ lead bot. Setup is one sitting at the PC, about 45 minutes. After that,
Claude reaches the PC through Remote Control and builds the bot from the app.

## 1. Copy this folder to the PC
Put `setup-windows.ps1` and `setup-ubuntu.sh` in `C:\milestone`.

## 2. Windows part (admin)
Right-click the Start button > **Terminal (Admin)** or **PowerShell (Admin)**:

```powershell
cd C:\milestone
Set-ExecutionPolicy -Scope Process Bypass
.\setup-windows.ps1
```

It writes `pc-info.txt` to the Desktop (CPU, board, virtualization), installs
Chrome, Tailscale, Ollama and Autologon, turns off sleep, and installs Ubuntu.
**Restart the PC.**

If Ubuntu fails with a virtualization error: restart into the BIOS (Del or F2
at boot) and enable **VT-x / Intel Virtualization** or **SVM / AMD-V**.

## 3. Ubuntu part
After the restart an Ubuntu window opens. Pick a username and password (write
them down), then:

```bash
bash /mnt/c/milestone/setup-ubuntu.sh
cd ~/milestone-leads && ~/.local/bin/claude
```

Sign in with the Milestone Claude account, accept the folder, type `/exit`.

## 4. Sign-ins
- **Tailscale** (tray icon): sign in with the same account as the Mac mini.
- **Autologon** (Start menu): enter your Windows password, click Enable. The PC
  then signs in by itself after updates or power cuts.
- **Chrome**: create a profile named "Lead bot".

## 5. Optional, in the BIOS
Set **Restore on AC power loss** to **Power On**, so the PC comes back after a
power cut without anyone pressing the button.

## 6. Done
Restart once more. A window titled **Milestone lead bot** opens by itself;
leave it open (minimizing is fine). Then tell Claude in the app, and send
`pc-info.txt` from the Desktop.
