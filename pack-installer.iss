; The optional Theme Pack installer: puts the .parkpack file where the
; installed Desktop Park looks for packs (%LOCALAPPDATA%\DesktopPark\packs).
; The app adds the pack's parks and pictures the next time it starts.
; release.ps1 builds the .parkpack (tools\build_pack.py) and passes these in.
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#ifndef MyAppPublisher
  #define MyAppPublisher "Desktop Park"
#endif
#ifndef MyAppURL
  #define MyAppURL "https://github.com/sirawitbm/desktop-park"
#endif

; the first Desktop Park that picks up packs
#define MinAppVersion "0.7.0"

[Setup]
AppId={{7C1E5B2A-4D8F-4B9E-9A31-6E2F0C8D5A17}
AppName=Desktop Park Theme Pack
AppVersion={#MyAppVersion}
AppVerName=Desktop Park Theme Pack {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
DefaultDirName={localappdata}\Programs\DesktopPark Theme Pack
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist\release
OutputBaseFilename=DesktopPark-ThemePack-v{#MyAppVersion}-Setup
SetupIconFile=assets\DesktopPark.ico
UninstallDisplayName=Desktop Park Theme Pack
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Desktop Park reads packs when it starts: it must be closed first
AppMutex=Local\DesktopPark

[Messages]
WelcomeLabel2=This adds the Theme Pack to Desktop Park: 7 ready-made parks (Sakura Garden, Forest Camp, Tropical Beach, Snowy Village, Countryside Farm, Under the Sea and Halloween Night) and 24 new pictures.%n%nYour own park and saved parks are not changed.
FinishedLabel=The Theme Pack is installed.%n%nOpen Desktop Park, press Parks on the board and pick a park.

[Files]
Source: "dist\release\DesktopPark-ThemePack-v{#MyAppVersion}.parkpack"; DestDir: "{localappdata}\DesktopPark\packs"; DestName: "theme-pack.parkpack"; Flags: ignoreversion

[Run]
Filename: "{code:MainExe}"; Description: "Open Desktop Park"; Flags: nowait postinstall skipifsilent; Check: MainExeExists

[Code]
const
  MainKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{2AF4DF58-FBA8-4EA8-877A-95FC34AE1AC2}_is1';

{ A value from Desktop Park's own uninstall entry ('' if it isn't installed). }
function MainValue(Name: String): String;
begin
  Result := '';
  if not RegQueryStringValue(HKCU, MainKey, Name, Result) then
    RegQueryStringValue(HKLM, MainKey, Name, Result);
end;

{ "0.7.0" -> 7000, so versions compare as numbers. }
function VersionNumber(S: String): Integer;
var
  I, Part, Count: Integer;
begin
  Result := 0;
  Part := 0;
  Count := 0;
  S := S + '.';
  for I := 1 to Length(S) do
    if S[I] = '.' then
    begin
      Result := Result * 1000 + Part;
      Part := 0;
      Count := Count + 1;
    end
    else if (S[I] >= '0') and (S[I] <= '9') then
      Part := Part * 10 + Ord(S[I]) - Ord('0');
  while Count < 3 do
  begin
    Result := Result * 1000;
    Count := Count + 1;
  end;
end;

function InitializeSetup(): Boolean;
var
  Installed: String;
begin
  Result := True;
  Installed := MainValue('DisplayVersion');
  if Installed = '' then
  begin
    SuppressibleMsgBox('Desktop Park is not installed yet.' + #13#10#13#10 +
      'Install Desktop Park first, then run this again.' + #13#10#13#10 +
      'Using the portable zip? Download the .parkpack file instead and import it ' +
      'with the folder button beside Parks on the board.', mbInformation, MB_OK, IDOK);
    Result := False;
  end
  else if VersionNumber(Installed) < VersionNumber('{#MinAppVersion}') then
  begin
    SuppressibleMsgBox('The Theme Pack needs Desktop Park {#MinAppVersion} or newer ' +
      '(this PC has ' + Installed + ').' + #13#10#13#10 +
      'Update Desktop Park first, then run this again.', mbInformation, MB_OK, IDOK);
    Result := False;
  end;
end;

function MainExe(Param: String): String;
begin
  Result := AddBackslash(MainValue('InstallLocation')) + 'DesktopPark.exe';
end;

function MainExeExists(): Boolean;
begin
  Result := FileExists(MainExe(''));
end;
