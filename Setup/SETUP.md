# Setup Guide

--- Welcome to this setup guide. ---        
Depending on your current situation, the setup for the Map Editor may take around 30 minutes to complete.
Please find all the (necessary) steps below

## Download 
[Python](https://www.python.org/downloads/) (required, tested on 3.10.7 & 3.12.1)     
[Visual Studio Code](https://code.visualstudio.com/download) (strongly recommended)      
[Blender](https://www.blender.org/download/) (strongly recommended, tested on 3.6 & 4.0)

## Installation
### Python
* Toggle `Add Python to PATH`
* Click on install

### Visual Studio Code
* Open the program
* Go to the Extensions tab (on the far left, or hold `Ctrl + Shift + X`)
* In the search bar, search and install the following extensions:
* * Pylance
* * Blender Development (by Jacques Lucke)
* * Better Comments (by Aaron Bond) [optional, recommended]

### Test Python & Install Required Libraries
* Double click on `CLICK ME.bat`
* This will run a simple Python test script and install all required Python libraries
* * If you get an error saying that `mathutils` cannot be installed, make sure you have Microsoft Visual C++ 14.0 or greater installed:  
https://visualstudio.microsoft.com/visual-cpp-build-tools/

### Install Blender-Python Libraries
* Since Blender uses its own Python interpreter, we must manually install a few libraries from the previous step into Blender's Python Environment
	
* First, locate the `python.exe` in your Blender installation. It may be located here:
* * (Regular)  
`C:\Program Files\Blender Foundation\Blender 4.0\4.0\python\bin\python.exe`	
* * (Steam)  
`E:\SteamLibrary\steamapps\common\Blender\4.0\python\bin\python.exe`	
			
* Now go back to the Map Editor folder, copy `powershell.exe`, and paste it in the Blender folder with the `python.exe`. If your system is asking for permissions, click on *continue*			
* Double click `powershell.exe` in the Blender folder. 
In here, copy & paste the commands below (one at a time) to install the libraries and click on enter:
```
python -m pip install psutil
python -m pip install matplotlib
```

Once the libraries are installed succesfully, you can exit the powershell program
				
				
### Connect Visual Studio Code to Blender
* Launch Visual Studio Code as an **administrator** and open the `MAP_EDITOR_ALPHA_v1.py`
* Here, click on the three-line menu icon at the top left corner. Then click on `File` and then click on `Add Folder to Workspace...` 
* Now make sure that the folder you Add / Select is `MM1-Map-Editor`. Once selected, click on `Add` at the bottom right of your menu window

// wip // 

* Go back to Visual Studio Code with the Editor open, and press "Ctrl + Shift + P"
			A search bar will appear at the top, in here, type "Blender"
			Now various options should appear, click on the one that reads "Blender: Start"
			This will start an instance of Blender, to which the Python script is connected
			
				To run the script, and import the test city in, again press "Ctrl + Shift + P" in Visual Studio Code
				Again type "Blender" and click on the option that reads "Blender: Run Script", this will execute the script
				
				Wait a couple seconds, and click on the Blender exe you had opened before
				Now you should see a test city in Blender, ready to be edited and build upon


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