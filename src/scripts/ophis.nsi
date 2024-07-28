; Script generated by the HM NIS Edit Script Wizard.

Unicode true
SetCompressor /SOLID lzma
RequestExecutionlevel admin

; HM NIS Edit Wizard helper defines
!define PRODUCT_NAME "Ophis"
!define PRODUCT_VERSION "2.2"
!define PRODUCT_PUBLISHER "Michael Martin"
!define PRODUCT_WEB_SITE "https://michaelcmartin.github.com/Ophis"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\ophis.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"
!define PRODUCT_STARTMENU_REGVAL "NSIS:StartMenuDir"

; MUI 1.67 compatible ------
!include "MUI.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Welcome page
!insertmacro MUI_PAGE_WELCOME
; License page
!define MUI_LICENSEPAGE_BUTTON "Install"
!define MUI_LICENSEPAGE_TEXT_BOTTOM "Press the Install button to continue."
!insertmacro MUI_PAGE_LICENSE "..\..\README"
; Directory page
!insertmacro MUI_PAGE_DIRECTORY
; Start menu page
var ICONS_GROUP
!define MUI_STARTMENUPAGE_NODISABLE
!define MUI_STARTMENUPAGE_DEFAULTFOLDER "Ophis"
!define MUI_STARTMENUPAGE_REGISTRY_ROOT "${PRODUCT_UNINST_ROOT_KEY}"
!define MUI_STARTMENUPAGE_REGISTRY_KEY "${PRODUCT_UNINST_KEY}"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "${PRODUCT_STARTMENU_REGVAL}"
!insertmacro MUI_PAGE_STARTMENU Application $ICONS_GROUP
; Instfiles page
!insertmacro MUI_PAGE_INSTFILES
; Finish page
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.txt"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"

; MUI end ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "Ophis-${PRODUCT_VERSION}-win64-installer.exe"
InstallDir "$PROGRAMFILES64\Ophis"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

Section "Ophis" SEC01
  SetDetailsPrint both
  SetOutPath "$INSTDIR"
  SetOverwrite try
  File /oname=README.txt "..\..\README"
  File /oname=WhatsNew.txt "..\..\WhatsNew"
  File "..\dist\ophis.exe"
  File "..\dist\libcrypto-1_1.dll"
  File "..\dist\libffi-7.dll"
  File "..\dist\libssl-1_1.dll"
  File "..\dist\tcl86t.dll"
  File "..\dist\tk86t.dll"
  File "..\dist\vcruntime140.dll"
  File "..\dist\vcruntime140_1.dll"
  File "..\dist\modules.zip"
  File "..\..\doc\ophismanual.pdf"
  SetOutPath "$INSTDIR\examples"
  File "..\..\examples\c64-1.oph"
  File "..\..\examples\petscii.map"
  File "..\..\examples\hello1.oph"
  File "..\..\examples\hello2.oph"
  File "..\..\examples\hello3.oph"
  File "..\..\examples\hello4a.oph"
  File "..\..\examples\hello4b.oph"
  File "..\..\examples\hello4c.oph"
  File "..\..\examples\hello5.oph"
  File "..\..\examples\hello6.oph"
  File "..\..\examples\hello7.oph"
  File "..\..\examples\structuredemo.oph"
  File "..\..\examples\fibonacci.oph"
  File "..\..\examples\kinematics.oph"
  File "..\..\examples\hello_a800.oph"
  File "..\..\examples\hello_apple2.oph"
  SetOutPath "$INSTDIR\examples\stella"
  File "..\..\examples\stella\hi_stella.oph"
  File "..\..\examples\stella\colortest.oph"
  File "..\..\examples\stella\README.txt"
  SetOutPath "$INSTDIR\examples\hello_nes"
  File "..\..\examples\hello_nes\hello_prg.oph"
  File "..\..\examples\hello_nes\hello_chr.oph"
  File "..\..\examples\hello_nes\hello_ines.oph"
  File "..\..\examples\hello_nes\hello_unif.oph"
  File "..\..\examples\hello_nes\README.txt"  
  SetOutPath "$INSTDIR\platform"
  File "..\..\platform\c64_0.oph"
  File "..\..\platform\c64kernal.oph"
  File "..\..\platform\c64header.oph"
  File "..\..\platform\libbasic64.oph"
  File "..\..\platform\vic20.oph"
  File "..\..\platform\vic20x.oph"
  File "..\..\platform\nes.oph"
  File "..\..\platform\stella.oph"
  File "..\..\platform\README.txt"
SectionEnd

Section -AdditionalIcons
  SetOutPath $INSTDIR
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
  CreateDirectory "$SMPROGRAMS\$ICONS_GROUP"
  CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\Manual.lnk" "$INSTDIR\ophismanual.pdf"
  CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\Uninstall.lnk" "$INSTDIR\uninst.exe"
  !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  SetRegView 64
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\ophis.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\ophis.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd


Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer."
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to completely remove $(^Name) and all of its components?" IDYES +2
  Abort
FunctionEnd

Section Uninstall
  !insertmacro MUI_STARTMENU_GETFOLDER "Application" $ICONS_GROUP
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\examples\hello_apple2.oph"
  Delete "$INSTDIR\examples\hello_a800.oph"
  Delete "$INSTDIR\examples\kinematics.oph"
  Delete "$INSTDIR\examples\structuredemo.oph"
  Delete "$INSTDIR\examples\fibonacci.oph"
  Delete "$INSTDIR\examples\hello7.oph"
  Delete "$INSTDIR\examples\hello6.oph"
  Delete "$INSTDIR\examples\hello5.oph"
  Delete "$INSTDIR\examples\hello4c.oph"
  Delete "$INSTDIR\examples\hello4b.oph"
  Delete "$INSTDIR\examples\hello4a.oph"
  Delete "$INSTDIR\examples\hello3.oph"
  Delete "$INSTDIR\examples\hello2.oph"
  Delete "$INSTDIR\examples\hello1.oph"
  Delete "$INSTDIR\examples\petscii.map"
  Delete "$INSTDIR\examples\c64-1.oph"
  Delete "$INSTDIR\ophis.exe"
  Delete "$INSTDIR\libcrypto-1_1.dll"
  Delete "$INSTDIR\libffi-7.dll"
  Delete "$INSTDIR\libssl-1_1.dll"
  Delete "$INSTDIR\tcl86t.dll"
  Delete "$INSTDIR\tk86t.dll"
  Delete "$INSTDIR\vcruntime140.dll"
  Delete "$INSTDIR\vcruntime140_1.dll"
  Delete "$INSTDIR\modules.zip"
  Delete "$INSTDIR\ophismanual.pdf"
  Delete "$INSTDIR\README.txt"
  Delete "$INSTDIR\examples\stella\hi_stella.oph"
  Delete "$INSTDIR\examples\stella\colortest.oph"
  Delete "$INSTDIR\examples\stella\README.txt"
  Delete "$INSTDIR\examples\hello_nes\hello_prg.oph"
  Delete "$INSTDIR\examples\hello_nes\hello_chr.oph"
  Delete "$INSTDIR\examples\hello_nes\hello_ines.oph"
  Delete "$INSTDIR\examples\hello_nes\hello_unif.oph"
  Delete "$INSTDIR\examples\hello_nes\README.txt"  
  Delete "$INSTDIR\platform\c64_0.oph"
  Delete "$INSTDIR\platform\c64kernal.oph"
  Delete "$INSTDIR\platform\c64header.oph"
  Delete "$INSTDIR\platform\libbasic64.oph"
  Delete "$INSTDIR\platform\vic20.oph"
  Delete "$INSTDIR\platform\vic20x.oph"
  Delete "$INSTDIR\platform\nes.oph"
  Delete "$INSTDIR\platform\stella.oph"
  Delete "$INSTDIR\platform\README.txt"

  Delete "$SMPROGRAMS\$ICONS_GROUP\Uninstall.lnk"
  Delete "$STARTMENU\Manual.lnk"

  RMDir "$SMPROGRAMS\$ICONS_GROUP"
  RMDir "$INSTDIR\examples\stella"
  RMDir "$INSTDIR\examples\hello_nes"
  RMDir "$INSTDIR\examples"
  RMDir "$INSTDIR\platform"
  RMDir "$INSTDIR"

  SetRegView 64
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  SetAutoClose true
SectionEnd
