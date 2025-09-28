#! /usr/bin/env python -t
'''
export drills in gcode for using on a milling machine
'''
__version__ = "1.0" ### please report bugs, suggestions etc at https://github.com/bkgoodman/InkscapeDrills ###

import os,sys,inkex,simplestyle,gettext,math
import csv
from copy import deepcopy
from inkex import elements


gcode_header = """
G17 G90  (XY Plane, Absolute Distance Mode)
G64 P 0.0050 Q 0.0000 (Path Blending)
{g_unit} (Units: G20=inches, G21=mm)
G54 (Set Work Offset)

G30 (Go to preset G30 location)

"""


gcode_footer = """
M30 (End of Program)
"""


# g_peck must include starting "Q" - make empty for no pecking
# g_drillcmd must be "G83" for pecking, or "G81" for straight drilling
gcode_drill_start="""
(--- Tool Setup ---)
G30 Z {z_clear} (Go in Z only to preset G30 location)
G30 (Go to preset G30 location)
T{toolno} M6  (Change Tool)
G43 H{toolno} Z{z_clear}  (apply tool length offset and move up)

S {g_rpm} M3 (Set Spindle RPM, Spindle ON, fwd)
M8 (Flood Coolant ON)

(--- Drill Setup ---)
G90 G98              (Absolute distance, return to initial plane)

G0 {firstpos}        (Go to first hole before plunging)
G0 Z{z_start}        (Go to and establish drill start position, height)

(--- Start {cycle} Cycle ---)
{g_drillcmd} Z{z_end} R{z_clear} {g_peck} F{z_feed}  (define and begin drill)

"""

gcode_drill_end="""
(--- End Drill Cycle ---)
G80 (Cancel Canned Drill Cycle)
M9 (All Coolant Off)
M5 (Spindle OFF)

G0 Z{z_clear} (Move to Clearence Height)
"""

hole_list_like = """
X1.0000 Y1.0000
"""

class DrillExport(inkex.Effect):
  def __init__(self):
      # Call the base class constructor.
      inkex.Effect.__init__(self)
      # Define options
      self.arg_parser.add_argument('--filename',action='store',type=str,
        dest='filename',default='',help='output filename')
      self.arg_parser.add_argument('--flipy',action='store',type=str,
        dest='flipy',help='Machine Orientation')
      self.arg_parser.add_argument('--separatedrills',action='store',type=str,
        dest='separatedrills',help='Separate files for each drill size')
      self.arg_parser.add_argument('--incrementtools',action='store',type=str,
        dest='incrementtools',help='Auto-Increment Tool Numbers for each size')
      self.arg_parser.add_argument('--unit',action='store',type=str,
        dest='unit',default='in',help='mm or in')
      self.arg_parser.add_argument('--scope',action='store',type=str,
        dest='scope',default='document',help='document, layer or selection')

      # GCode parameters
      self.arg_parser.add_argument('--toolno',action='store',type=int,
        dest='toolno',default=1,help='Tool Number')
      self.arg_parser.add_argument('--rpm',action='store',type=int,
        dest='rpm',default=1,help='Spindle Speed (RPM)')
      self.arg_parser.add_argument('--zfeed',action='store',type=float,
        dest='zfeed',default=1,help='Z Feed Rate')
      self.arg_parser.add_argument('--zclear',action='store',type=float,
        dest='zclear',default=1,help='Clearance (Fast Traverse) Z-Height')
      self.arg_parser.add_argument('--zstart',action='store',type=float,
        dest='zstart',default=1,help='Drill start height')
      self.arg_parser.add_argument('--zend',action='store',type=float,
        dest='zend',default=1,help='Drill end depth')
      self.arg_parser.add_argument('--peck',action='store',type=float,
        dest='peck',default=0,help='Peck depth (zero for no peck)')
      self.arg_parser.add_argument('--spottoolno',action='store',type=int,
        dest='spottoolno',default=0,help='Spot Tool Nuber (zero for no spot drilling)')
      self.arg_parser.add_argument('--spotzend',action='store',type=float,
        dest='spotzend',default=0,help='Spot Tool depth (zero for no peck)')

  def process_circle(self,circle):
        cx = circle.get('cx',0)
        cy = circle.get('cy',0)
        r = circle.get('r',0)
        cx_uu = self.svg.unittouu(f"{cx}{self.svg.unit}")
        cy_uu = self.svg.unittouu(f"{cy}{self.svg.unit}")
        r_uu = self.svg.unittouu(f"{r}{self.svg.unit}")
        matrix = circle.composed_transform()
        cx_abs, cy_abs = matrix.apply_to_point([cx_uu, cy_uu])

        if self.flipy == 'true':
            cy_abs = self.heightDoc - cy_abs

        if self.unit == "mm":
            cx_mm = self.svg.uutounit(cx_abs,'mm')
            cy_mm = self.svg.uutounit(cy_abs,'mm')
            r_mm = self.svg.uutounit(r_uu,'mm')
            formatted_d = f"{r_mm * 2:.2f}"
            formatted_cx = f"{cx_mm:.2f}"
            formatted_cy = f"{cy_mm:.2f}"
        else:
            cx_in = self.svg.uutounit(cx_abs,'in')
            cy_in = self.svg.uutounit(cy_abs,'in')
            r_in = self.svg.uutounit(r_uu,'in')
            formatted_d = f"{r_in * 2:.4f}"
            formatted_cx = f"{cx_in:.4f}"
            formatted_cy = f"{cy_in:.4f}"
        return ({
            "d": formatted_d,
            "cx": formatted_cx,
            "cy": formatted_cy,
            })

  def find_circles_recursively(self, root_node, circle_groups):
        """
        Recursively walks the SVG element tree to find all circle nodes.
        """
        # inkex.utils.errormsg(f"ROOT TAG {root_node.tag} vs {elements._polygons.Circle.tag}")
        # The tag is checked against the specific Circle class tag
        if isinstance(root_node, elements.Circle):
            e = self.process_circle(root_node)
            circle_groups.setdefault(e['d'], []).append(e)
        
        # Iterate over all children of the current node

        for child in root_node:
            # inkex.utils.errormsg(f"FIND node {child}")
            self.find_circles_recursively(child, circle_groups)

  def effect(self):
    #log ("This is a test")
    svg = self.document.getroot()
    
    ns_svg = inkex.NSS['svg']

    doc_unit = self.svg.unit

    # Get the attributes:
    self.heightDoc = self.svg.unittouu(self.svg.get('height'))
    self.widthDoc = self.svg.unittouu(self.svg.get('width'))

    fn = self.options.filename
    self.unit = self.options.unit
    self.flipy = self.options.flipy
    scope = self.options.scope
    separatedrills = self.options.separatedrills
    
    circle_groups = {}


    if scope == "selection":
        # The `self.svg.selection` property provides the currently selected elements.
        for node in self.svg.selection.values():
            self.find_circles_recursively(node, circle_groups)
    elif scope == "layer":
        # Get the currently active layer
        current_layer = self.svg.get_current_layer()
        if current_layer is not None:
            self.find_circles_recursively(current_layer, circle_groups)
    elif scope == "document":
        # The root of the SVG document is `self.document`.
        self.find_circles_recursively(self.document.getroot(), circle_groups)
    

    if self.unit == "mm":
        g_unit = "G21"
    else:
        g_unit = "G20"

    if (self.options.peck == 0):
        g_peck = ""
        g_drillcmd = "G81"
    else:
        g_peck = f"{self.options.peck:.4f}"
        g_drillcmd = "G83"
    g_rpm = f"{int(self.options.rpm)}"
    toolno = self.options.toolno
    z_start = f"{self.options.zstart:.4f}"
    z_end = f"{self.options.zend:.4f}"
    z_clear = f"{self.options.zclear:.4f}"
    z_feed = f"{self.options.zfeed:.4f}"

    # Define our drill operation
    operations = [
            {
                'name': "Peck" if g_peck != "" else "Drill",
                'spot': False,
                'peck': g_peck,
                'drillcmd' : g_drillcmd,
                'toolno': 0, # Fill in later
                'zend': z_end
                }
            ]
    if (self.options.spottoolno != 0) and (self.options.spotzend):
        # Add a spot drill operation at beginning
        operations.insert(0,{
                'name': "Spot",
                'spot': True,
                'peck': "",
                'drillcmd' : "G81",
                'toolno': self.options.spottoolno,
                'zend': f"{self.options.spotzend:.4f}"

            })
        do_spot_drill = True
    else:
        do_spot_drill = False


    if (self.options.zclear <= self.options.zstart):
        inkex.utils.errormsg("Z-Clear must be ABOVE Z-Start")
        return

    if (self.options.zstart <= self.options.zend):
        inkex.utils.errormsg("Z-End must be BELOW Z-Start. (Z-End should often be negative)")
        return

    if (len(circle_groups) == 0):
        inkex.utils.errormsg("No circles found in the specified scope.")
    else:
        if separatedrills == "true":
            # One CSV per radius
            for d, hole_list in circle_groups.items():
                base,ext = os.path.splitext(fn)
                if not ext:
                    ext = ".csv"
                nfn = f"{base}_{d}{self.unit}{ext}"
                with open(nfn, "w", newline="") as ncfile:
                    ncfile.write(f"(--- {base} - {d}{self.unit} - Tool # {toolno} ---)\n")
                    if do_spot_drill:
                        ncfile.write(f"(Tool {self.options.spottoolno}  - Center/Spot drill)\n")
                    ncfile.write(gcode_header.format(g_unit=g_unit))
                    for op in operations:
                        if op['spot']:
                            t = op['toolno']
                            ncfile.write(f"(Tool {t}  - Spot Drill)\n")
                        else:
                            t = toolno
                            ncfile.write(f"(Tool {t}  - {d}{self.unit})\n")
                        ncfile.write(gcode_drill_start.format(z_start=z_start,
                            cycle=op['name'],
                            z_end=op['zend'],
                            z_clear=z_clear,
                            z_feed=z_feed,
                            firstpos=f"X{hole_list[0]['cx']} Y{hole_list[0]['cy']}",
                            g_drillcmd=op['drillcmd'],
                            g_peck=op['peck'],
                            g_rpm=g_rpm,
                            toolno=toolno))
                        for hole in hole_list:
                            ncfile.write(f"X{hole['cx']} Y{hole['cy']}\n")
                        ncfile.write(gcode_drill_end.format(z_clear=z_clear))
                    ncfile.write(gcode_footer)
                if (self.options.incrementtools == "true"):
                    toolno += 1
        else:
            # All circles in one CSV
            diameters = circle_groups.keys()
            with open(fn, "w", newline="") as ncfile:
                ncfile.write(f"(--- {fn} - All Drills ---)\n")
                if do_spot_drill:
                    ncfile.write(f"(--- Tool {self.options.spottoolno}  - Center/Spot drill ---)\n")
                for (x,d) in enumerate(diameters):
                    ncfile.write(f"(--- Tool {toolno+x}  - {d}{self.unit} ---)\n")
                ncfile.write(gcode_header.format(g_unit=g_unit))

                first_drill = False
                for op in operations:
                    for d in diameters:
                        if op['spot']:
                            t = op['toolno']
                        else:
                            t = toolno
                            ncfile.write(f"(Tool {t}  - {d}{self.unit})\n")

                        #ncfile.write(f"(Tool {t}  Operation {op['name']} - {d}{self.unit})\n")

                        # Tool change only for new diameter, or FIRST spot diameter, only
                        # (i.e. don't change for every different spot drill diameter

                        hole_list = circle_groups[d]
                        if not op['spot'] or not first_drill:
                            first_drill = True
                            ncfile.write(gcode_drill_start.format(z_start=z_start,
                                cycle=op['name'],
                                z_end=op['zend'],
                                z_clear=z_clear,
                                z_feed=z_feed,
                                g_drillcmd=op['drillcmd'],
                                g_peck=op['peck'],
                                firstpos=f"X{hole_list[0]['cx']} Y{hole_list[0]['cy']}",
                                g_rpm=g_rpm,
                                toolno=t))

                        for hole in hole_list:
                            ncfile.write(f"X{hole['cx']} Y{hole['cy']}\n")
                        # We'll end spot drills after ALL diameters done
                        if not op['spot']:
                            ncfile.write(gcode_drill_end.format(z_clear=z_clear))
                        if (self.options.incrementtools == "true") and not op['spot']:
                            toolno += 1
                    # All diameters done - end, if we are doing spot drills
                    if op['spot']:
                        ncfile.write(gcode_drill_end.format(z_clear=z_clear))
                ncfile.write(gcode_footer)
    return

# Create effect instance and apply it.
effect = DrillExport()
effect.run()
