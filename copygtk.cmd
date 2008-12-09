xcopy /e /i c:\gtk\etc dist\py2exe\etc
xcopy /e /i c:\gtk\share dist\py2exe\share
xcopy /e /i c:\gtk\lib dist\py2exe\lib
del /s /q dist\py2exe\share\locale\*    
