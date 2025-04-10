param (
    [int]$numClients = 2  # Number of clients to launch (default: 2)
)

# Load necessary libraries
Add-Type -AssemblyName System.Windows.Forms
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class User32 {
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
}
"@ -Language CSharp

function Set-WindowFocus($processName) {
    Start-Sleep -Milliseconds 500
    $proc = Get-Process | Where-Object { $_.ProcessName -like $processName } | Select-Object -First 1
    if ($proc -and $proc.MainWindowHandle -ne 0) {
        [User32]::SetForegroundWindow($proc.MainWindowHandle)
        Start-Sleep -Milliseconds 200
    }
}

# Server address
$serverIP = "localhost"

# Launch clients with unique names
for ($i = 1; $i -le $numClients; $i++) {
    $agentName = "$i"

    # Open a new window and run the client
    $scriptPath = "cd <path_to_I_like_trains-public>; .\venv\Scripts\activate; python -m client"
    $process = Start-Process powershell -PassThru -ArgumentList "-NoExit", "-Command `"$scriptPath`""

    # Pause to ensure the window is opened
    Start-Sleep -Milliseconds 800
}
