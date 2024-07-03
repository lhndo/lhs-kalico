

# ResHelper - DK Edition
A series of scripts designed to streamline Klipper's resonance testing workflow


### What does this do?

It auto generates the resonance graph, and outputs the graph images into the config folder. These can be viewed directly in Mainsail/Fluid.<br>
The Damping Ratio is automatically computed and displayed in the console and appended to the graph image filename.<br>
Throughout the process there is no need to connect to the PI by SSH or SFTP.

### DK Features

Example: `RESONANCE_TEST_Y ACCEL_PER_HZ=180 MIN_FREQ=40 MAX_FREQ=140 DAMPING_RATIO=0 CLASSIC=1`

* **ACCEL_PER_HZ** (0-300..) - Default config value - Sets the accel per hz value
* **MIN_FREQ** (0-200..) - Default config value - Sets minimum test frequency
* **MAX_FREQ** (0-200..) - Default config value - Sets maximum test frequency
* **DR** - (**0**/1) - Default 0 . Enables damping ratio calculation.
  * This procedure is compute intensive and slows down testing. Recommended for final value generation only
* **CLASSIC** - (0/**1**) - Default 1 
  * DK BEv2 introduced a new series of algorithms which produce different outputs and recommendations compared to the mainline Klipper implementation and cannot be evaluated against previous known data. This option restores the classic graph generation functionality and is enabled by default.   


<br>

## Installation:

#### 1. Install Configuration 

`cd klipper/LHS_Tools/ResHelper`<br>
`./install.sh`  (or manually copy reshelper_dk.cfg into your printer_data/config folder)

<br>

#### 2. Install Rscript (Optional if you want to run damping_ratio calculations )

`sudo apt install r-base`<br>
`sudo Rscript install_rs_lib.R`

<br> Note: *If the library install fails, try installing a Fortran compiler: `sudo apt-get install gfortran` then rerun `sudo Rscript install_rs_lib.R`*   

<br>

#### 3. Include the configuration file in your printer.cfg

`[include reshelper_dk.cfg]` <br>
❗**Note: 
Check your home folder path in **reshelper_dk.cfg**   
If your host user name is not "biqu", then you have to change the paths in reshelper_dk.cfg**

<br>

#### 6. Restart Klipper


<br>




## Usage
<hr>

#### 1. Run the Resonance Test Macros 
Run **RESONANCE_TEST_X** or **RESONANCE_TEST_Y** macros and wait for the Console output.

#### 2. View the graph images directly in the browser by going to MACHINE (Mainsail) and then opening the RES_DATA folder.
*The files are placed in ~/printer_data/config/RES_DATA/*<br>
<img src="https://raw.githubusercontent.com/lhndo/ResHelper/main/Images/config.png"/><br>
<img src="https://raw.githubusercontent.com/lhndo/ResHelper/main/Images/graph.png" width=50%/>
<br>
*The damping ratio is displayed in the Console and appended to the filename.*<br><br>

<img src="https://raw.githubusercontent.com/lhndo/ResHelper/main/Images/console.png"/>


#### 3. Add the resonance test results to your printer.cfg 
**Example:**
<pre><code>
[input_shaper]

shaper_freq_x: 68.2
shaper_type_x: mzv
damping_ratio_x: 0.055

shaper_freq_y: 54.0
shaper_type_y: zv
damping_ratio_y: 0.0523
</code></pre>

*For more information please consult: https://www.klipper3d.org/Resonance_Compensation.html*

<br>

*Enjoy!*
<br>
<br>

*Based on work by **Dmitry**, **churls** and **kmobs***<br>
https://gist.github.com/kmobs/3a09cc28ec79e62f28d8db2179be7909

## Support
<br>
<a href='https://ko-fi.com/lh_eng' target='_blank'><img height='46' style='border:0px;height:36px;' src='https://az743702.vo.msecnd.net/cdn/kofi3.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' />
