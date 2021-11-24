# Plot current meter

## Overview

This script takes raw files from a current meter and creates rose plots for each station them. It also generates a summary .csv table which can be used for
reporting.

This script was created to plot data from current meters that are attached to a CPT during cable route surveys.

## Work instruction
To easily identify the plots make sure the raw files are named like the CPT stations (2EU-Y-CP01).

User has to manually add a **path to a input folder** (in_dir) with current meter raw data, add a **project output name** (projectname) for the summary .csv 
(i.e. 2EUROPA E13 S12.csv), a **path to a output folder** (out_dir) and choose the **model of the curent meter** (currentmeter_modell) used.

![Code of user input example](https://github.com/holgerson11/Plot-current-meter/blob/master/Figures/code_user_input.png?raw=true)

Currently supported current meter models:
- Nortek Aquadopp   (currentmeter_model = 0)
- Midas ECM         (currentmeter_model = 1)

The script will then try to find where the CPT was on the seabed for each individual push. If multiple pushes have been made, 
the script will add a letter to the station name, to match the CPT push (i.e. 2EU-Y-CP01A, 2EU-Y-CP01B ...)

## Dependencies
- pandas
- matplotlib
- numpy
- scipy
