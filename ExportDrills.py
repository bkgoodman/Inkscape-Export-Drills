#! /usr/bin/env python -t
'''
export drills in csv for using on a milling machine
'''
__version__ = "1.0" ### please report bugs, suggestions etc at https://github.com/bkgoodman/InkscapeDrills ###

import os,sys,inkex,simplestyle,gettext,math
import csv
from copy import deepcopy
from inkex import elements
_ = gettext.gettext

linethickness = 1 # default unless overridden by settings

def log(text):
  if 'BKG_LOG' in os.environ:
    f = open(os.environ.get('BKG_LOG'), 'a')
    f.write(text + "\n")


class DrillExport(inkex.Effect):
  def __init__(self):
      # Call the base class constructor.
      inkex.Effect.__init__(self)
      # Define options
      self.arg_parser.add_argument('--csvfile',action='store',type=str,
        dest='csvfile',default='',help='output filename')
      self.arg_parser.add_argument('--flipy',action='store',type=str,
        dest='flipy',help='Machine Orientation')
      self.arg_parser.add_argument('--unit',action='store',type=str,
        dest='unit',default='in',help='mm or in')
      self.arg_parser.add_argument('--scope',action='store',type=str,
        dest='scope',default='document',help='document, layer or selection')

  def find_circles_recursively(self, root_node, found_list):
        """
        Recursively walks the SVG element tree to find all circle nodes.
        """
        # inkex.utils.errormsg(f"ROOT TAG {root_node.tag} vs {elements._polygons.Circle.tag}")
        # The tag is checked against the specific Circle class tag
        #if root_node.tag == elements._polygons.Circle.tag:
        if isinstance(root_node, elements.Circle):
            # inkex.utils.errormsg(f"IS CIRCLE")
            found_list.append(root_node)
        
        # Iterate over all children of the current node

        for child in root_node:
            # inkex.utils.errormsg(f"FIND node {child}")
            self.find_circles_recursively(child, found_list)
  def effect(self):
    #log ("This is a test")
    svg = self.document.getroot()
    
    ns_svg = inkex.NSS['svg']

    doc_unit = self.svg.unit

    # Get the attributes:
    heightDoc = self.svg.unittouu(self.svg.get('height'))
    widthDoc = self.svg.unittouu(self.svg.get('width'))
    #inkex.utils.errormsg(f"Doc units: {doc_unit} docWidth={widthDoc} heightDoc={heightDoc}")

    fn = self.options.csvfile
    unit = self.options.unit
    flipy = self.options.flipy
    scope = self.options.scope
    
    #inkex.utils.errormsg(f"Page width {widthDoc} Page height {heightDoc}")
    #inkex.utils.errormsg(f'Page width {self.svg.to_dimensional(widthDoc,"in")} Page height {self.svg.to_dimensional(heightDoc,"in")}')

    #inkex.utils.errormsg(f"Testing {fn} {flipy} {unit}")
    with open(fn, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Diameter",'X', 'Y'])


        found_circles = []


        if scope == "selection":
            # The `self.svg.selection` property provides the currently selected elements.
            for node in self.svg.selection.values():
                self.find_circles_recursively(node, found_circles)
        elif scope == "layer":
            # Get the currently active layer
            current_layer = self.svg.get_current_layer()
            if current_layer is not None:
                self.find_circles_recursively(current_layer, found_circles)
        elif scope == "document":
            # The root of the SVG document is `self.document`.
            self.find_circles_recursively(self.document.getroot(), found_circles)
        

        # Process the found circles
        if found_circles:
            for circle in found_circles:
                circle.style["fill"] = "blue"
                circle.style["stroke"] = "none"
                cx = circle.get('cx',0)
                cy = circle.get('cy',0)
                r = circle.get('r',0)
                cx_uu = self.svg.unittouu(f"{cx}{doc_unit}")
                cy_uu = self.svg.unittouu(f"{cy}{doc_unit}")
                r_uu = self.svg.unittouu(f"{r}{doc_unit}")
                if flipy == 'true':
                    cy_uu = heightDoc - cy_uu
                if unit == "mm":
                    cx_mm = self.svg.uutounit(cx_uu,'mm')
                    cy_mm = self.svg.uutounit(cy_uu,'mm')
                    r_mm = self.svg.uutounit(r_uu,'mm')
                    formatted_d = f"{r_mm * 2:.2f}"
                    formatted_cx = f"{cx_mm:.2f}"
                    formatted_cy = f"{cy_mm:.2f}"
                    #inkex.utils.errormsg(f"TO : {formatted_cx} {formatted_cy} {formatted_d}")
                else:
                    cx_in = self.svg.uutounit(cx_uu,'in')
                    cy_in = self.svg.uutounit(cy_uu,'in')
                    r_in = self.svg.uutounit(r_uu,'in')
                    formatted_d = f"{r_in * 2:.4f}"
                    formatted_cx = f"{cx_in:.4f}"
                    formatted_cy = f"{cy_in:.4f}"
                    #inkex.utils.errormsg(f"TO : {formatted_cx} {formatted_cy} {formatted_d}")
                writer.writerow([formatted_d, formatted_cx, formatted_cy])
        else:
            inkex.utils.errormsg("No circles found in the specified scope.")
    return

"""
        for node in svg.selection:
                try:
                    # Get the bounding box of the selected object
                    inkex.utils.errormsg(f"CLRCLE {node} {inkex.Circle.tag} {node.tag}")
                    bb = node.bounding_box()
                    
                    # Calculate the center point
                    center_x = (bb.x + bb.width / 2)
                    center_y = (bb.y + bb.height / 2)
                    inkex.utils.errormsg(f"{node}")
                    
                    # Apply the object's transform to the center point
                    transform = node.transform
                    point = inkex.Point(center_x, center_y)
                    transformed_point = transform.apply_to_point(point)

                    writer.writerow([transformed_point.x, transformed_point.y])

                except Exception as e:
                    inkex.utils.errormsg(f"Could not process object: {node.get('id')}. Error: {e}")

"""
    

    

# Create effect instance and apply it.
effect = DrillExport()
effect.run()
