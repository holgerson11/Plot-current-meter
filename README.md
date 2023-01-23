# Plot current meter

## Overview

This script takes raw files from a current meter and creates rose plots for each station. It also generates a summary .csv table which can be used for
reporting.

This script was created to plot data from current meters that are attached to a CPT during cable route surveys.

## Work instruction
To easily identify the plots make sure the raw files are named like the CPT stations (2EU-Y-CP01).

User has to manually add a **path to a input folder** (in_dir) with current meter raw data, add a **project output name** (projectname) for the summary .csv 
(i.e. 2EUROPA E13 S12.csv), a **path to a output folder** (out_dir) and choose the **model of the curent meter** (currentmeter_modell) used.

```
# USER INPUT
in_dir = r'E:\Project\current meter raw data'
out_dir = r'E:\Project\current meter raw data\output'

projectname = '2EUROPA E13 B12'  # name of your project for output i.e. 2AF East E14 B01.csv
currentmeter_model = 1           # 0 = Nortek Aquadopp, 1 = Midas ECM

# CUT-OFF VALUES (in [m])
# Default values: Midas ECM: 0.3 / 0.05, Nortek Auqadopp: 5 / 1
if currentmeter_model == 0:
    max_depth_delta = 5          # cut-off limit from max. depth of raw file 
    max_depth_noise = 1          # cut-off limit for noise in depth
elif currentmeter_model == 1:
    max_depth_delta = 0.3
    max_depth_noise = 0.05

# CUT-OFF VALUES (in [s])
min_push_duration = 60          # min. duration on seabed to count as single push

# SCALE
max_current_speed = 0.3         # max current speed in m/s, adjust to scale colorbar
```
Currently supported current meter models:
- Nortek Aquadopp   (currentmeter_model = 0)
- Midas ECM         (currentmeter_model = 1)

The script will then try to find where the CPT was on the seabed for each individual push. If multiple pushes have been made, 
the script will add a letter to the station name, to match the CPT push (i.e. 2EU-Y-CP01A, 2EU-Y-CP01B ...)

## Output examples
### Midas ECM from shallow water (Two CPT pushes)
![Rose plot example](https://user-images.githubusercontent.com/10484392/143293370-374c8070-19ee-44be-a799-78335363a776.png)
![Rose plot example](https://user-images.githubusercontent.com/10484392/143293664-0f00c9de-8439-43f6-bbfd-5f87841fb2d5.png)
### Debug plot
![Debug plot example](https://user-images.githubusercontent.com/10484392/143293701-f05e7b5e-22c0-40ff-855f-4ec6057100ea.png)

### Nortek Aquadopp from deep water
![Rose plot example](https://user-images.githubusercontent.com/10484392/143293827-3ebb034e-2a68-4aff-a76c-02acaff91ba0.png)
### Debug plot
![Debug plot example](https://user-images.githubusercontent.com/10484392/143293901-2c435386-5aa8-4503-90e2-3f7681994495.png)

## Dependencies
- pandas
- matplotlib
- numpy
- scipy
