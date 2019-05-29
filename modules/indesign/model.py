import xml.etree.ElementTree as ET

import modules.lib.commons as commons


class IndesignModel:
    def __init__(self):
        pass

    @staticmethod
    def get_transformations(root, page):
        for iterator in root.iter():
            if iterator.tag == "TextFrame":
                transformations = [
                    float(i) for i in iterator.get("ItemTransform").split(" ")
                ]
        print(transformations)

    @staticmethod
    def setup_page(root):
        page = {}

        for iterator in root.iter():
            if iterator.tag == "Page":
                dimensions = [
                    float(i) for i in iterator.get("GeometricBounds").split(" ")
                ]
                page["width"] = dimensions[3]
                page["height"] = dimensions[2]

        return page

    def process_spreads(self, args, package):
        output = ""

        for spread in package.spreads:
            tree = ET.parse(args.extract + spread)
            root = tree.getroot()

            page = self.setup_page(root)
            self.get_transformations(root, page)

            for iterator in root.iter():
                if iterator.tag == "TextFrame":
                    story = iterator.get("ParentStory")
                    story = "Stories/Story_" + story + ".xml"

                    if story in package.stories:
                        output += self.process_story(args, story, package)

                if iterator.tag == "Rectangle":
                    outerStyle = "display: inline-block; overflow:hidden;"
                    innerStyle = ""

                    border_radius = commons.get_image_border_radius(iterator.attrib)
                    outerStyle += border_radius
                    for properties in iterator.iter():
                        if properties.tag == "PathGeometry":
                            size, width, height = commons.get_image_container_size(
                                properties
                            )
                            outerStyle += (
                                "width:"
                                + size["width"]
                                + ";height:"
                                + size["height"]
                                + ";"
                            )

                        if properties.tag == "FrameFittingOption":
                            frame = commons.get_image_framing(
                                properties.attrib, iterator
                            )
                            innerStyle += frame

                        if properties.tag == "BlendingSetting":
                            opacity = commons.get_image_opacity(properties.attrib)
                            innerStyle += opacity

                        if properties.tag == "Link":
                            for link in properties.iter():
                                if link.tag == "Link":
                                    imageUrl = commons.process_image(
                                        link.attrib.get("LinkResourceURI"),
                                        outerStyle,
                                        innerStyle,
                                    )
                                    output += imageUrl

        return output

    @staticmethod
    def process_story(args, story, package):
        tree = ET.parse(args.extract + story)
        root = tree.getroot()

        htmlContent = ""

        for paragraphStyleRange in root.iter("ParagraphStyleRange"):
            # Get the text alignment
            alignment = paragraphStyleRange.attrib.get("Justification")
            alignment = commons.get_alignment(alignment)
            listItemParagraph = paragraphStyleRange.attrib.get(
                "BulletsAndNumberingListType"
            )

            if listItemParagraph:
                if listItemParagraph == "BulletList":
                    listStyle = "<p style='" + alignment + ";'><ul>"
                else:
                    listStyle = "<p style='" + alignment + ";'><ol>"

                for characterStyleRange in paragraphStyleRange.iter(
                    "CharacterStyleRange"
                ):
                    for child in characterStyleRange.iter():
                        if child.tag == "Content":
                            listStyle += "<li>" + child.text + "</li>"

                        if child.tag == "Br":
                            listStyle += "<br />"

                if listItemParagraph == "BulletList":
                    listStyle += "</ul></p>"
                else:
                    listStyle += "</ol></p>"
                htmlContent += listStyle

            else:
                paragraghStyle = "<p style='" + alignment + ";'>"
                for characterStyleRange in paragraphStyleRange.iter(
                    "CharacterStyleRange"
                ):

                    characterStyle = ""

                    # Get the font style
                    fontStyle = characterStyleRange.attrib.get("FontStyle")
                    fontStyle = commons.get_font_weight(fontStyle)

                    # Get the font size
                    fontSize = characterStyleRange.attrib.get("PointSize")
                    fontSize = commons.get_font_size(fontSize)

                    # Get the font color
                    fontColor = characterStyleRange.attrib.get("FillColor")
                    fontColor = commons.get_color(fontColor, package, args)

                    # Get the storke color
                    strokeColor = characterStyleRange.attrib.get("StrokeColor")
                    strokeColor = commons.get_stroke_color(strokeColor, package, args)

                    # Get the Underline style
                    underline = characterStyleRange.attrib.get("Underline")

                    # Get the StrikeThrough style
                    strikeThrough = characterStyleRange.attrib.get("StrikeThru")

                    background = (
                        "padding: 0 .3em;background-color: rgb(255,235,59)"
                        if strikeThrough
                        else ""
                    )

                    strikeThrough = commons.get_strike_through(strikeThrough)

                    # Get the font family
                    fontFamily = commons.get_font_family(None)

                    # Get the line height
                    lineHeight = commons.get_line_height(None)

                    # Get the Image url
                    imageUrl = ""
                    for child in characterStyleRange.iter():
                        if child.tag == "Rectangle":
                            for properties in child.iter():
                                if properties.tag == "Image":
                                    for link in properties.iter():
                                        if link.tag == "Link":
                                            imageUrl = commons.process_image(
                                                link.attrib.get("LinkResourceURI")
                                            )
                                            characterStyle += imageUrl

                        if child.tag == "Properties":
                            for properties in child.iter():
                                if properties.tag == "Leading":
                                    lineHeight = commons.get_line_height(
                                        properties.text
                                    )

                                if properties.tag == "AppliedFont":
                                    fontFamily = commons.get_font_family(
                                        properties.text
                                    )
                        if child.tag == "Content":
                            characterStyle += "<span "
                            characterStyle += (
                                "style='" + fontStyle + ";" if fontStyle else ""
                            )
                            characterStyle += fontColor + ";" if fontColor else ""
                            characterStyle += strokeColor + ";" if strokeColor else ""
                            characterStyle += underline + ";" if underline else ""
                            # characterStyle += strikeThrough + ";" if strikeThrough else ""
                            characterStyle += fontFamily + ";" if fontFamily else ""
                            characterStyle += lineHeight + ";" if lineHeight else ""
                            characterStyle += fontSize + ";" if fontSize else ""
                            characterStyle += background + ";" if strikeThrough else ""
                            characterStyle += "'>" + child.text if child.text else "'>"
                            characterStyle += "</span>"

                        if child.tag == "Br":
                            characterStyle += "<br />"

                    # Append character style to paragraph style
                    paragraghStyle += characterStyle

                # Close the paragraph style
                paragraghStyle += "</p>"
                htmlContent += paragraghStyle

        return htmlContent

