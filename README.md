# Inkscape-Export-Drills
Inkscape extension to export circle drill coordinates to CSV file

# Install

Install `.py` and `.inx` file in a new folder inside you Inkscape User Extensions folder. Restart Inkscape

# Use
Go to menu `Extensions->CNC Tools->Export Drills...`

It's pretty obvious, but:

* Will allow you to export **Circle** objects only. i.e. Must be round, not elipses, not paths.
* Exports center coordinate and drill/hole/circle diameter to CSV file of your choosing
* Allows you to specify units to export in
* Has a "Flip Y Coordinate" checkbox, which is important because most CNC machines are Y-Up, and SVG (Inkscape) is Y-Down. When using this, the (0,0) origin will be the lower left corder of your Inkscape document. (First, if multiple pages?)
