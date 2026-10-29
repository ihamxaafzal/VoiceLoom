#ifndef PayloadDir
  #define PayloadDir "..\payload"
#endif
#ifndef ReleaseDir
  #define ReleaseDir "..\..\outputs"
#endif
[Setup]
AppId={{B4C2A07D-D160-47B9-AF78-150F208DB7AE}
AppName=VoiceLoom
AppVersion=1.0.0
AppPublisher=VoiceLoom
DefaultDirName={localappdata}\Programs\VoiceLoom
DefaultGroupName=VoiceLoom
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={#ReleaseDir}
OutputBaseFilename=VoiceLoom-Setup-1.0.0-Windows-x64
SetupIconFile=assets\voice-narrator.ico
UninstallDisplayIcon={app}\VoiceLoom.exe
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
DisableWelcomePage=no
InfoBeforeFile=INSTALL-NOTES.txt
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\VoiceLoom"; Filename: "{app}\VoiceLoom.exe"
Name: "{group}\Uninstall VoiceLoom"; Filename: "{uninstallexe}"
Name: "{autodesktop}\VoiceLoom"; Filename: "{app}\VoiceLoom.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\VoiceLoom.exe"; Description: "Launch VoiceLoom"; Flags: nowait postinstall skipifsilent
