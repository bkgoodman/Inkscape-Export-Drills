# Inkscape-Export-Drills
Two extensions:
* **Export Drills** -  Exports circile centers to CSV files
* **GCode Drills** - Generates GCode files for dilling circles

Inkscape extension to export circle drill coordinates to CSV file. This is particularly usefull for taking Inkscape designs (for things like PCBs), which you would then want to drill on something like a CNC milling machine.

# Install

Install `.py` and `.inx` (and `.png`) file in a new folder inside you Inkscape User Extensions folder. Restart Inkscape. 

It may be easier to grab the newest release from ZIP files from "Releases" in Githib.

# Use
Go to menu `Extensions->CNC Tools->Export Drills...` or `Extensions->CNC Tools->GCode Drills...`

It's pretty obvious, but:

* Will allow you to export **Circle** objects only. i.e. Must be round, not elipses, not paths.
* Exports center coordinate and drill/hole/circle diameter to CSV file of your choosing
* Allows you to specify units to export in
* Has a "Flip Y Coordinate" checkbox, which is important because most CNC machines are Y-Up, and SVG (Inkscape) is Y-Down. When using this, the (0,0) origin will be the lower left corder of your Inkscape document. (First, if multiple pages?)
* "Seperate Drill Files" checkbox will generate separate CSV files for each drill size, with the size appended to the filename.
 
# GCode Drills
GCode export was designed around Tormach XSTech Router - but at least in theory should (mostly) work for others. In addition to everything above, it has features to:

* Enable optional pecking (if desired)
* Optional spot/center drilling
* Specify separate tool numbers for different sizes, and/or center drilling
