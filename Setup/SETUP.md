# Setup Guide

Depending on your current situation, the setup for the Map Editor may take around 30 minutes to complete.  
Please complete all the steps below.

## Download 
[Python](https://www.python.org/downloads/) (required, tested on multiple versions)   
[Visual Studio Code](https://code.visualstudio.com/download) (strongly recommended)      
[Blender](https://www.blender.org/download/) (strongly recommended, tested on multiple versions) 

## Installation
### Python
* Click on `Add Python to PATH` in the Setup Wizard and then choose Install

### Test Python & Install Required Libraries
* Double click on `CLICK ME.bat` to start the process
* * If you get an error stating that `mathutils` cannot be installed, download [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/). After launching this program, toggle `Desktop development with C++` and click on Install at the botto mright corner.

### Install Blender-Python Libraries
* Since Blender uses its own Python interpreter, we must manually install a few libraries from the previous step into Blender's Python Environment
	
* First, locate the `python.exe` in your Blender installation. It may be located here:
* (Default)  
```
C:\Program Files\Blender Foundation\Blender 4.0\4.0\python\bin\python.exe
```	

* (Steam)
```
E:\SteamLibrary\steamapps\common\Blender\4.0\python\bin\python.exe
```
			
* Now go back to the Map Editor folder, copy `powershell.exe`, and paste it in the Blender folder with the `python.exe`. If your system is asking for permission, click on *continue*			
* Next, doucle click `powershell.exe` in the Blender folder and copy & paste the following lines in the terminal (one at a time) and press enter.
```
python -m pip install psutil
python -m pip install matplotlib
```

Once the libraries are installed succesfully, you can exit the powershell program
				
### Connect Visual Studio Code to Blender
* Launch Visual Studio Code as **administrator** and open `MAP_EDITOR_ALPHA_v1.py`
* Next, click on the three-line menu icon at the top left corner. Then click on `File` and then on `Add Folder to Workspace...` 
* Now make sure that the folder you select is `MM1-Map-Editor` and you click on `Add` at the bottom right of explorer menu
* Go back to Visual Studio Code with the `MAP_EDITOR_ALPHA_v1.py` open, and hold `Shift + Q`

![Preview](Resources/EditorResources/GALLERY/OPEN_BLENDER_EXE_VIA_VSCODE.png)

* Click on a Blender executable if available, or click on `Choose a new Blender executable...` and navigate to e.g.:
`C:\Program Files\Blender Foundation\Blender 3.6` and select the `blender.exe`
* Now press `Shift + Q` (again) and select your chosen Blender executable, the application will now start
* If you see the following message in Visual Studio Code, it means VScode and Blender have succesfully connected:

![Preview](Resources/EditorResources/GALLERY/SUCCES_VSCODE_CONNECT_TO_BLENDER.png)

* Next, (in VScode), hold `Shift + W`, the Map Editor will now start processing
* **Only** and **only** if you see a message very similar to this:

![Preview](Resources/EditorResources/GALLERY/SUCCES_RAN_PYTHON_BLENDER_CODE.png)

* it means that the script has *fully* and *succesfully* ran





BUILDING "YOUR FIRST" CITY
	Open "MAP_EDITOR_ALPHA_v1.py" with Visual Studio Code
	Press CONTROL + F and search for "Bookmark"
		Here you'll find city polygons that I have prepared advance
		Feel free to change or add any, or leave it as is
			Next, go to the top of the script, around line 60, and review the default settings in SETUP I & II 
			
			Next, exit the script and start "powershell.exe" in the editor's folder
			In the powershell console type "python MAP_EDITOR_ALPHA_v1.py" and press enter
			Alternatively, you can type "python map[TAB]" (pressing TAB on your keyboard will autofill the script's name)
			
				The Editor will now generate all necessary city files and create the final .AR file
				In the powershell console you should see a "loading screen bar" that goes up to 100 %
				This loading bar is however (unfortunately) not indicative of the script completing without errors
				Only when at the bottom of the console you see "Succesfully created {name_of_city} in {time}" the editor has finished execution
					Depending on your chosen settings, the game may now immediately boot
			
				
### Closing Notes
	The previous steps should fully prepare you for installing all the software tools and libraries, as well as connecting everything
	Additional information on how to best leverage the power of the Editor (e.g. with keybindings)  will be provided in a future update
	
~~~