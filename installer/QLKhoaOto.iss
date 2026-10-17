; Bộ cài Windows — Quản lý khóa ô tô CSHN
; Dựng tự động bằng GitHub Actions (.github/workflows/build-windows.yml)
#ifndef MyVersion
  #define MyVersion "0.0.0"
#endif

[Setup]
AppId={{6E3B7C2A-9D41-4F2B-8C55-QLKHOAOTOCSHN}
AppName=Quản lý khóa ô tô CSHN
AppVersion={#MyVersion}
AppVerName=Quản lý khóa ô tô CSHN {#MyVersion}
AppPublisher=CSHN
AppPublisherURL=https://github.com/HP-wukoong/QUAN_LY_KHOA_OTO_CSHN
AppSupportURL=https://github.com/HP-wukoong/QUAN_LY_KHOA_OTO_CSHN/releases
; Cài theo người dùng, không cần quyền Admin; thư mục ghi được (dữ liệu nằm cạnh tool)
PrivilegesRequired=lowest
DefaultDirName={userpf}\QLKhoaOto
DisableDirPage=no
DisableProgramGroupPage=yes
UsePreviousAppDir=yes
OutputDir=..\dist
OutputBaseFilename=QLKhoaOto_Setup_{#MyVersion}
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\QLKhoaOto.exe
UninstallDisplayName=Quản lý khóa ô tô CSHN
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng ngoài Desktop"; GroupDescription: "Biểu tượng:"

[Files]
Source: "..\dist\QLKhoaOto.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\QLKhoaOto\server.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\QLKhoaOto\app.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\QLKhoaOto\DOC_TRUOC_HUONG_DAN.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Quản lý khóa ô tô CSHN"; Filename: "{app}\QLKhoaOto.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"
Name: "{autoprograms}\Thư mục dữ liệu QLKhoaOto"; Filename: "{app}"
Name: "{autodesktop}\Quản lý khóa ô tô"; Filename: "{app}\QLKhoaOto.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\QLKhoaOto.exe"; Description: "Mở Quản lý khóa ô tô ngay"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; KHÔNG xóa data\ và backups\ — gỡ cài đặt vẫn giữ dữ liệu học viên
Type: files; Name: "{app}\*.new"

[Messages]
WelcomeLabel2=Bộ cài sẽ cài [name/ver] vào máy.%n%nDữ liệu học viên lưu trong thư mục cài đặt (data\ và backups\). Nếu đã dùng bản cũ ở thư mục khác (vd D:\QLKhoaOto) hãy chọn ĐÚNG thư mục đó ở bước sau để giữ nguyên dữ liệu.
