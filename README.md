# qt-config
IWAST Configuration Tool

# How to use FBS

Make sure that:
- You use the terminal of Pycharm (really easier...)
- You have correctly installed the fbs library
- You have correctly installed NSIS on your computer (you can download it here: https://nsis.sourceforge.io/Download)
- You need to specify the path of the NSIS application in your Windows path environment variable
- You must work with the version 5.9.2 of PyQt5
- You must use Python 3.6 (not an higher version)


When all requirements are met, you can start a new project with FBS:
1. Execute the following command: fbs startproject
2. Put all your python files in the src/main/python directory
3. You can specify some parameters in the file "base.json" (src/build/settings/base.json)
4. To create an .exe file, execute the following command: fbs freeze 
5. To create an installation file, execute the following command: fbs installer 

If all is well, your installation file should be in the "target" repository
