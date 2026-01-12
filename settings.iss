[Setup]
AppName=YazarPress Pro
AppVersion=4.0
DefaultDirName={autopf}\YazarPress Pro
DefaultGroupName=YazarPress Pro
SetupIconFile=C:\Users\volkano\yazarpress\favicon.ico
Compression=lzma
SolidCompression=yes
OutputDir=C:\Users\volkano\Desktop

[Files]
; Ana EXE dosyası
Source: "C:\Users\volkano\yazarpress\dist\YazarPress_Pro\YazarPress_Pro.exe"; DestDir: "{app}"; Flags: ignoreversion
; Klasörün içindeki tüm kütüphane ve DLL dosyaları
Source: "C:\Users\volkano\yazarpress\dist\YazarPress_Pro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\YazarPress Pro"; Filename: "{app}\YazarPress_Pro.exe"; IconFilename: "{app}\YazarPress_Pro.exe"