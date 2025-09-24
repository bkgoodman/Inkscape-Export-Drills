#! /usr/bin/env python -t
'''
export drills in csv for using on a milling machine
'''
__version__ = "1.0" ### please report bugs, suggestions etc at https://github.com/bkgoodman/InkscapeDrills ###

import os,sys,inkex,simplestyle,gettext,math
import csv
from copy import deepcopy
from inkex import elements

class DrillExport(inkex.Effect):
  def __init__(self):
      # Call the base class constructor.
      inkex.Effect.__init__(self)
      # Define options
      self.arg_parser.add_argument('--csvfile',action='store',type=str,
        dest='csvfile',default='',help='output filename')
      self.arg_parser.add_argument('--flipy',action='store',type=str,
        dest='flipy',help='Machine Orientation')
      self.arg_parser.add_argument('--separatedrills',action='store',type=str,
        dest='separatedrills',help='Separate files for each drill size')
      self.arg_parser.add_argument('--unit',action='store',type=str,
        dest='unit',default='in',help='mm or in')
      self.arg_parser.add_argument('--scope',action='store',type=str,
        dest='scope',default='document',help='document, layer or selection')

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

    fn = self.options.csvfile
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
    
    if (len(circle_groups) == 0):
        inkex.utils.errormsg("No circles found in the specified scope.")
    else:
        if separatedrills == "true":
            # One CSV per radius
            for d, rows in circle_groups.items():
                base,ext = os.path.splitext(fn)
                if not ext:
                    ext = ".csv"
                nfn = f"{base}_{d}{self.unit}{ext}"
                with open(nfn, "w", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["X", "Y"])
                    for row in rows:
                        writer.writerow([row['cx'],row['cy']])
        else:
            # All circles in one CSV
            with open(fn, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Diameter", "X", "Y"])
                for rows in circle_groups.values():
                    for row in rows:
                        writer.writerow([row['d'], row['cx'],row['cy']])
    return

# Create effect instance and apply it.
effect = DrillExport()
effect.run()
