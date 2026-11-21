$ffmpegDir = "C:\Users\jcvse\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.1-full_build\bin"
$pyScripts = "C:\Users\jcvse\AppData\Local\Programs\Python312\Scripts"
$currPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if ($currPath -notmatch [regex]::Escape($ffmpegDir)) {
    [System.Environment]::SetEnvironmentVariable("Path", "$currPath;$ffmpegDir;$pyScripts", "User")
    Write-Host "PATH do usuario atualizado com sucesso!"
} else {
    Write-Host "Caminhos ja configurados no PATH."
}
