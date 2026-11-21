$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("C:\Users\jcvse\Desktop\Pasta CENTRAL SHORTS.lnk")
$Shortcut.TargetPath = "C:\Users\jcvse\podcast_cutter"
$Shortcut.Description = "Acesso direto a pasta do projeto Central Shorts"
$Shortcut.Save()
Write-Host "Atalho da pasta criado na Area de Trabalho com sucesso!"
