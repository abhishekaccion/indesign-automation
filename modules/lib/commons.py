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
    return "object-fit: none;"


def get_image_framing(properties, iterator):
    switcher = {
        "FillProportionally": handle_cover,
        "Proportionally": handle_contain,
        "ContentToFrame": handle_fill,
        "default": handle_default,
    }

    return switcher.get(properties["FittingOnEmptyFrame"], switcher["default"])(
        properties, iterator
    )


def get_image_opacity(properties):
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


def get_image_container_size(properties):
    size = {}
    width = []
    height = []

    for path in properties.iter("PathPointType"):
        points = path.attrib["Anchor"].split(" ")
        if not float(points[0]) in width:
            width.append(float(points[0]))
        if not float(points[1]) in height:
            height.append(float(points[1]))

    size["width"] = str(-(width[0] - width[1])) + "pt"
    size["height"] = str(-(height[0] - height[1])) + "pt"

    return size, width, height


def get_alignment(args):
    # Function to get text alignment : defaults to left
    switcher = {
        "CenterAlign": "text-align: center",
        "RightAlign": "text-align: right",
        "LeftAlign": "text-align: left",
    }

    return switcher.get(args, switcher["LeftAlign"])


def get_font_weight(args):
    # Function to get font weight : defaults to normal
    switcher = {
        "Bold": "font-weight: bold",
        "Italic": "font-style: italic",
        "Normal": "font-weight: normal",
        "Bold Italic": "font-style: italic; font-weight: bold",
    }

    return switcher.get(args, switcher["Normal"])


def get_font_size(args):
    # Function to get font size : defaults to 12pt
    return "font-size: " + args + "pt" if args else "font-size: 12pt"


def get_font_family(args):
    # Function to get font family: defaults to minion pro
    return "font-family:" + args if args else "font-family: Minion Pro"


def get_line_height(args):
    # Function to get line height: defaults to 14.4pt
    return "line-height:" + args + "pt" if args else "line-height: 14.4pt"


def get_color(color, package, args):
    tree = ET.parse(args.extract + package.graphic.name)

    color_str = "rgb(0, 0, 0)"
    for i in tree.getroot().iter("Color"):
        if i.attrib["Self"] == color:
            colorValue = i.attrib["ColorValue"].split(" ")
            rgb_col = []
            for x in range(4):
                if x < len(colorValue):
                    rgb_col.append(int(colorValue[x]))
                else:
                    rgb_col.append(0)
            color_str = "rgb" + str(decode_color.cmyk_to_rgb(*rgb_col))

    return "color:" + color_str


def get_stroke_color(color, package, args):
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

    return "-webkit-text-stroke: 2px " + currentColor if currentColor else None


def get_text_decoration(args):
    return "text-decoration: underline" if args else None


def get_strike_through(args):
    return "text-decoration: line-through" if args else None


def process_image(url, outer, inner):
    url = unquote(url).split(":")
    with open(url[1], "rb") as f:
        b = base64.b64encode(f.read())
    return (
        "<span style='"
        + outer
        + "'><img style='"
        + inner
        + "' src='data:image/png;base64,"
        + str(b).split("'")[1]
        + "'/></span>"
    )

