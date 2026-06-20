#define MyAppName "YouTube Downloader"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "janleague"
#define MyAppURL "https://github.com/janleague/youtube-downloader"
#define MyAppExeName "YouTubeDownloader.exe"

[Setup]
AppId={{7FC5F45E-95E2-4B32-980B-0C7FE26D3A84}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={localappdata}\Programs\YouTube Downloader
DefaultGroupName=YouTube Downloader
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=YouTubeDownloader-Setup-v{#MyAppVersion}
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
LicenseFile=LICENSE
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Modern YouTube MP3 and MP4 downloader
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "installffmpeg"; Description: "FFmpeg'i winget ile kur (MP3 ve yüksek kaliteli MP4 için önerilir)"; GroupDescription: "Ek bileşenler:"; Flags: checkedonce

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\YouTube Downloader"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"
Name: "{group}\GitHub sayfası"; Filename: "{#MyAppURL}"
Name: "{group}\Kaldır"; Filename: "{uninstallexe}"
Name: "{autodesktop}\YouTube Downloader"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon

[Run]
Filename: "winget.exe"; Parameters: "install --id Gyan.FFmpeg --exact --silent --accept-package-agreements --accept-source-agreements"; StatusMsg: "FFmpeg kuruluyor..."; Flags: runhidden waituntilterminated skipifdoesntexist; Tasks: installffmpeg
Filename: "{app}\{#MyAppExeName}"; Description: "YouTube Downloader'ı başlat"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
