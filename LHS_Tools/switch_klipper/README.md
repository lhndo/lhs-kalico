## Switch Klipper


This script automates switching between klipper mainline (default) and danger klipper
This switch is done by renaming the klipper folders and the configuration file.  


## Setup

:warning: Backup your klipper configuration first by downloading a copy of ~/printer_data/config/ 


### Requirements

1. **Copy script to home folder:**

```
cd ~/klipper/LHS_Tools/switch_klipper/
chmod +x switch_klipper.sh
cp switch_klipper.sh ~/
cd ~
```

2. **File Structure Setup**



* Currently running danger klipper, you should have the following:  

> Folders: **klipper/, klipper_dk/**  
> Files: **printer.cfg, printer.cfg.dk**  


* Currently running klipper mainline (default):  

> Folders: **klipper/, klipper_ml/**  
> Files: **printer.cfg, printer.cfg.ml**  

## Usage

To switch to danger klipper

```
sudo ./switch_klipper.dk ml
```

To switch to klipper mainline

```
sudo ./switch_klipper.dk dk
```
<br>