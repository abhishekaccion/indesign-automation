import glob
import imageio
import xml.etree.ElementTree as ET
import modules.lib.decode_color as decode_color
from urllib.parse import unquote
import base64


def get_image_position(attrib, iterator):
    style = ""
    container = {}

    for properties in iterator.iter():
        if properties.tag == "PathGeometry":
            size, container_width, container_height = get_image_container_size(
                properties
            )

        if properties.tag == "Image":
            transformation = get_image_transformation(properties.attrib)

            for item in properties.iter():
                if item.tag == "GraphicBounds":
                    container["width"] = float(item.attrib["Bottom"])
                    container["height"] = float(item.attrib["Right"])

    style += "object-position: "
    style += str(float(transformation[4]) - container_width[0]) + "pt" + " "
    style += str(float(transformation[5]) - container_height[0]) + "pt;"

    if attrib.get("TopCrop") or attrib.get("LeftCrop"):
        style += "width: 100%;"
        style += (
            "height: " + str(float(transformation[3]) * container["height"]) + "pt;"
        )
    else:
        style = "width: 100%; height: 100%;"
        style += "object-position: "
        style += str(float(transformation[4]) - container_width[0]) + "pt" + " "
        style += str(float(transformation[5]) - container_height[0]) + "pt;"

    return style


def get_image_border_radius(attrib):
    return (
        "border-radius:" + attrib["CornerRadius"] + "pt;"
        if attrib.get("CornerRadius")
        and attrib.get("TopLeftCornerOption") == "RoundedCorner"
        else "border-radius: 0pt;"
    )


def handle_cover(attrib, iterator):
    return "object-fit: cover;" + get_image_position(attrib, iterator)


def handle_contain(attrib, iterator):
    return "object-fit: contain;" + get_image_position(attrib, iterator)


def handle_fill(attrib, iterator):
    return "object-fit: fill;" + get_image_position(attrib, iterator)


def handle_default(attrib, iterator):
    return ""


def get_image_framing(properties, iterator):
    switcher = {
        "FillProportionally": handle_cover,
        "Proportionally": handle_contain,
        "ContentToFrame": handle_fill,
        "default": handle_default,
    }
    
    if properties.get("FittingOnEmptyFrame") != None and hasattr(
        properties.get("FittingOnEmptyFrame"), "__call__"
    ):
        return properties.get("FittingOnEmptyFrame")(properties, iterator)
    else:
        return switcher["default"](properties, iterator)


def BlendingSetting(properties, package=None, args=None):
    return (
        "opacity:" + str(int(properties["Opacity"]) / 100) + ";"
        if properties.get("Opacity")
        else "opacity: 1;"
    )


def get_image_transformation(properties):
    return (
        properties["ItemTransform"].split(" ")
        if properties.get("ItemTransform")
        else [0, 0, 0, 0, 0, 0]
    )

def ptToPx(val):
    print("&&&&&&&&&&&&",float(val),float(val)/72,float(val)/72*96)
    return float(val)/72*96

def get_image_container_size(properties):
    size = {}
    width = []
    height = []

    for path in properties.iter("PathPointType"):
        print("****************",path.attrib)
        points = path.attrib["Anchor"].split(" ")
        if not float(points[0]) in width:
            width.append(float(points[0]))
        if not float(points[1]) in height:
            height.append(float(points[1]))
    print("*******123******",width,height)        
    size["width"] = str(ptToPx(-(width[0] - width[1]))) + "px"
    size["height"] = str(ptToPx(-(height[0] - height[1]))) + "px"

    return size, width, height


def Justification(val, package=None, args=None):
    # Function to get text alignment : defaults to left
    switcher = {
        "CenterAlign": "text-align: center",
        "RightAlign": "text-align: right",
        "LeftAlign": "text-align: left",
        "LeftJustified": "display: flex; justify-content: end",
        "CenterJustified": "display: flex; justify-content: center",
        "RightJustified": "display: flex; justify-content: flex-end",
        "ToBindingSide": "display: flex; justify-content: end",
        "AwayFromBindingSide": "display: flex; justify-content: flex-end",
        "FullyJustified": "text-align: justify",
    }

    return switcher.get(val, switcher["LeftAlign"])

def FontStyle(val, package=None, args=None):
    # Function to get font weight : defaults to normal
    switcher = {
        "Bold": "font-weight: bold",
        "Italic": "font-style: italic",
        "Regular": "font-weight: normal",
        "Bold Italic": "font-style: italic; font-weight: bold",
    }

    return switcher.get(val, val)

def Capitalization(val, package=None, args=None):
    # Function to get font weight : defaults to normal
    switcher = {
        "AllCaps": "text-transform: uppercase",
        "SmallCaps": "text-transform: uppercase"
    }

    return switcher.get(val, "")

def Position(val, package=None, args=None):
    # Function to get font weight : defaults to normal
    switcher = {
        "Superscript": "vertical-align: super; font-size: 58% !important",
        "Subscript": "vertical-align: sub; font-size: 58% !important"
    }

    return switcher.get(val, "")    

def LeftIndent(val, package=None, args=None):
    # Function to get font size : defaults to 12pt
    return f"padding-left: {val}px"

def RightIndent(val, package=None, args=None):
    # Function to get font size : defaults to 12pt
    return f"padding-right: {val}px"

def FirstLineIndent(val, package=None, args=None):
    # Function
    return f"text-indent: {val}px"

def SpaceBefore(val, package=None, args=None):
    # Function
    return f"padding-top: {val}px"

def SpaceAfter(val, package=None, args=None):
    # Function
    return f"padding-bottom: {val}px"

def ParagraphBorderOn(val, package=None, args=None):
    # Function to get font size : defaults to 12pt
    return f"border: 1px solid"

def Underline(val, package=None, args=None):
    # Function to get font size : defaults to 12pt
    return f"text-decoration: underline"

def StrikeThru(val, package=None, args=None):
    return "text-decoration: line-through" if val else None

def PointSize(val, package=None, args=None):
    # Function to get font size : defaults to 12pt
    return f"font-size: {val}pt" if val else "font-size: 12pt"

def VerticalScale(val, package=None, args=None):
    # Function to get font size : defaults to 12pt
    return f"display: inline-block;transform: scaleY({round(float(val))/100})"

def HorizontalScale(val, package=None, args=None):
    # Function to get font size : defaults to 12pt
    return f"display: inline-block;transform: scaleX({round(float(val))/100})"

def AppliedFont(val, package=None, args=None):
    # Function to get font family: defaults to minion pro
    return "font-family:" + val if val else "font-family: Minion Pro"


def Leading(val, package=None, args=None):
    # Function to get line height: defaults to 14.4pt
    return "line-height:" + val + "pt" if val else "line-height: 14.4pt"
    # return "padding-top:" + val + "pt" if val else "line-height: 14.4pt"

# def StrokeWeight(val, package=None, args=None):
#     # Function to get StrokeWeight
#     return f"{val}pt"

def FillColor(color, package, args):
    tree = ET.parse(args.extract + package.graphic.name)

    color_str = "rgb(0, 0, 0)"
    for i in tree.getroot().iter("Color"):
        if i.attrib["Self"] == color:
            colorValue = i.attrib["ColorValue"].split(" ")
            rgb_col = []
            for x in range(4):
                if x < len(colorValue):
                    rgb_col.append(int(float(colorValue[x])))
                else:
                    rgb_col.append(0)
            color_str = "rgb" + str(decode_color.cmyk_to_rgb(*rgb_col))

    return "color:" + color_str


def StrokeColor(color, package, args):
    tree = ET.parse(args.extract + package.graphic.name)

    currentColor = None

    for i in tree.getroot().iter("Color"):
        if i.attrib["Self"] == color:
            colorValue = i.attrib["ColorValue"].split(" ")
            currentColor = "rgb" + str(
                decode_color.cmyk_to_rgb(
                    float(colorValue[0]),
                    float(colorValue[1]),
                    float(colorValue[2]),
                    float(colorValue[3]),
                )
            )

    # return "-webkit-text-stroke: " + currentColor if currentColor else None
    return "background: " + currentColor if currentColor else None


def get_text_decoration(args):
    return "text-decoration: underline" if args else None




def process_image(url, outer="", inner=""):
    url = unquote(url).split(":")
    print("-----img----",url[1])
    with open(url[1], "rb") as f:
        b = base64.b64encode(f.read())
    return f"""<span style='{outer} display: block; margin: auto'>
        <img style='{outer} display: block; margin: auto; align:center;' 
        src='data:image/png;base64,{str(b).split("'")[1]}'/>
        </span>"""

