' ===============================
' Run Python App from /src
' ===============================

Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Thư mục gốc project (nơi đặt file VBS)
rootDir = FSO.GetParentFolderName(WScript.ScriptFullName)

' Python trong virtual environment
pythonExe = rootDir & "\.venv\Scripts\pythonw.exe"

' Main script trong src
mainScript = rootDir & "\src\main.py"

' Kiểm tra tồn tại
If Not FSO.FileExists(pythonExe) Then
    MsgBox "Không tìm thấy pythonw.exe trong .venv", 16, "Lỗi"
    WScript.Quit
End If

If Not FSO.FileExists(mainScript) Then
    MsgBox "Không tìm thấy src\main.py", 16, "Lỗi"
    WScript.Quit
End If

' Set working directory về root project
WshShell.CurrentDirectory = rootDir

' Chạy chương trình (0 = ẩn console)
WshShell.Run """" & pythonExe & """ """ & mainScript & """", 0, False

Set WshShell = Nothing
Set FSO = Nothing
