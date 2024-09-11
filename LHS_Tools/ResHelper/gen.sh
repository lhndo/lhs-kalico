#!/bin/sh

# Define paths as variables
RES_DATA_PATH="$HOME/printer_data/config/RES_DATA"
DR_R_PATH="$HOME/klipper/LHS_Tools/ResHelper/DR.R"
TMP_PATH="/tmp"

echo "\nResHelper DK: Generating Data...\n"
name="shaper_calibrate_$1"
[ ! -d "$RES_DATA_PATH" ] && mkdir -p "$RES_DATA_PATH"

# Graph generation
if [ "$3" -eq 0 ]; then
    # Use default generation
    echo "ResHelper DK: Starting DK Graph Generation...\n"
    ~/klipper/scripts/calibrate_shaper.py "$TMP_PATH"/resonances_"$1"_*.csv -o "$RES_DATA_PATH"/shaper_calibrate_"$1".png
elif [ "$3" -eq 1 ]; then
    # Classic klipper generation
    echo "ResHelper DK: Starting Classic Klipper Graph Generation...\n"
    ~/klipper/scripts/calibrate_shaper_classic.py "$TMP_PATH"/resonances_"$1"_*.csv -o "$RES_DATA_PATH"/shaper_calibrate_"$1".png --shapers zv,mzv,ei --classic true
else
    # Handle unexpected values of $3
    echo "Invalid value for third argument: $3. Expected 0 or 1."
    exit 1
fi

# Damping ratio
if [ "$2" -eq 1 ]; then 
    echo "ResHelper DK: Calculating damping ratio for $1"
    dr=$(Rscript "$DR_R_PATH")
    dr=${dr#"[1] "}
    echo "ResHelper DK: Damping ratio for $1 calculated:\n damping_ratio_$1: $dr\n "
fi

# Cleanup
name="$name-dr_${dr:-NA}-v$(date "+%Y%m%d_%H%M").png"
mv "$RES_DATA_PATH"/shaper_calibrate_"$1".png "$RES_DATA_PATH/$name"
find "$TMP_PATH" -name "resonances_*.csv" -print 2>/dev/null -exec rm {} \;
echo "ResHelper DK: Finished\n"