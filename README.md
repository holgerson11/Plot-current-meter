# Plot-current-meter-

PLOT CURRENT METER

This script takes current meter raw files and creates rose plots for each station them. It also generates a summary .csv table which can be used for
reporting.

This was created to plot data from current meters that are attached to a CPT during cable route surveys.

User has to manually define station names and depth ranges for each station (as start and stop line numbers in raw file)
i.e.: 'S1-FG-CP01':     {'file': 'CPT_01.dat', 'start_line': 69, 'stop_line': 420},
(Please note: For Midas ECM use true line number in raw file, header will be subtracted by script)

User has to manually choose from which currentmeter model recorded the raw files
Currently supported:
- Nortek Aquadopp
- Midas ECM
