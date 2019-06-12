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

            # page = self.setup_page(root)
            # self.get_transformations(root, page)
            for story_iterator in root.iter():
                if story_iterator.tag == "TextFrame":
                    story = story_iterator.get("ParentStory")
                    story = "Stories/Story_" + story + ".xml"

                    if story in package.stories:
                        output += self.process_story(args, story, package)

                if story_iterator.tag == "Rectangle":
                    outerStyle = "display: inline-block; overflow:hidden;"
                    innerStyle = ""

                    border_radius = commons.get_image_border_radius(
                        story_iterator.attrib
                    )
                    outerStyle += border_radius
                    for properties in story_iterator.iter():
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
                                properties.attrib, story_iterator
                            )
                            innerStyle += frame

                        if properties.tag == "BlendingSetting":
                            opacity = commons.BlendingSetting(properties.attrib)
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

            paragraphStyleList = {}

            for paragraph_attr in paragraphStyleRange.attrib:
                print("##paragraph_attr : ",paragraph_attr,paragraphStyleRange.attrib.get(paragraph_attr))
                if hasattr(commons, paragraph_attr):
                    attr_function = getattr(commons, paragraph_attr)
                    paragraphStyleList[paragraph_attr] = attr_function(
                        paragraphStyleRange.attrib.get(paragraph_attr), package, args
                    )

            # Get the text alignment
            # alignment = paragraphStyleRange.attrib.get("Justification")
            # alignment = commons.get_alignment(alignment)

            paraStyle = "; ".join(list(paragraphStyleList.values()))
            listItemParagraph = paragraphStyleRange.attrib.get(
                "BulletsAndNumberingListType"
            )

            if listItemParagraph:
                # if listItemParagraph == "BulletList":
                #     listStyle = f"<p style='{paraStyle}'><ul>"
                # else:
                #     listStyle = f"<p style='{paraStyle}'><ol>"

                for characterStyleRange in paragraphStyleRange.iter(
                    "CharacterStyleRange"
                ):
                    print("###LI characterStyleRange : ",characterStyleRange,characterStyleRange.attrib )
                    listItem=""
                    for child in characterStyleRange.iter():
                        if child.tag == "Content":
                            listItem += "<li>" + child.text + "</li>"
                            print("---Text---",child.text)
                        
                if "LeftIndent" in paragraphStyleList:
                    listStyle = f" padding-inline-start "+ paragraphStyleList.get("LeftIndent")[paragraphStyleList.get("LeftIndent").find(":"):]+";"
                if listItemParagraph == "BulletList":
                    htmlContent += f"<span><ul style='{listStyle}'>{listItem}</ul></span>"
                else:
                    htmlContent += f"<span><ol style='{lineStyle}'>{listItem}</ol></span>"        

            else:
                paragraghStyle = f"<p style='{paraStyle}'>"

                for characterStyleRange in paragraphStyleRange.iter(
                    "CharacterStyleRange"
                ):
                    print("### characterStyleRange : ",characterStyleRange,characterStyleRange.attrib )
                    characterStyle = ""
                    characterStyleDict = {
                        "FontStyle": "font-weight: normal",
                        "FillColor": "color:rgb(0, 0, 0)",
                        "AppliedFont": commons.AppliedFont(None),
                        "Leading": commons.Leading(None),
                        "PointSize": "font-size: 12pt",
                    }

                    for char_attr in characterStyleRange.attrib:
                        print("##char attr :  ",char_attr,characterStyleRange.attrib.get(char_attr))
                        if hasattr(commons, char_attr):
                            attr_function = getattr(commons, char_attr)
                            characterStyleDict[char_attr] = attr_function(
                                characterStyleRange.attrib.get(char_attr), package, args
                            )

                    # Get the font style
                    # fontStyle = characterStyleRange.attrib.get("FontStyle")
                    # fontStyle = commons.get_font_weight(fontStyle)

                    # Get the font size
                    # fontSize = characterStyleRange.attrib.get("PointSize")
                    # fontSize = commons.get_font_size(fontSize)

                    # Get the font color
                    # fontColor = characterStyleRange.attrib.get("FillColor")
                    # fontColor = commons.get_color(fontColor, package, args)

                    # Get the storke color
                    # strokeColor = characterStyleRange.attrib.get("StrokeColor")
                    # strokeColor = commons.get_stroke_color(strokeColor, package, args)

                    # Get the Underline style
                    underline = characterStyleRange.attrib.get("Underline")

                    # Get the StrikeThrough style
                    strikeThrough = characterStyleRange.attrib.get("StrikeThru")

                    background = (
                        "padding: 0 .3em;background-color: rgb(255,235,59)"
                        if strikeThrough
                        else ""
                    )
                    characterStyleDict["background"] = background
                    strikeThrough = commons.StrikeThru(strikeThrough)

                    # Get the font family
                    # fontFamily = commons.get_font_family(None)

                    # Get the line height
                    # lineHeight = commons.get_line_height(None)

                    # Get the Image url
                    imageUrl = ""
                    for child in characterStyleRange.iter():
                        # if child.tag == "Rectangle":
                        #     for properties in child.iter():
                        #         print("^^^^^properties^^^^^",properties,properties.attrib)
                        #         if properties.tag == "Image":
                        #             for link in properties.iter():
                        #                 print("*******link*******",link,link.attrib)
                        #                 if link.tag == "Link":
                        #                     imageUrl = commons.process_image(
                        #                         link.attrib.get("LinkResourceURI")
                        #                     )
                        #                     characterStyle += imageUrl

                        if child.tag == "Rectangle":
                            outerStyle = "display: inline-block; overflow:hidden;"
                            innerStyle = ""

                            border_radius = commons.get_image_border_radius(
                                child.attrib
                            )
                            outerStyle += border_radius
                            for properties in child.iter():
                                print("------child props------",properties,properties.attrib)
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
                                    print("%%%%%%%%%%%%%%%%%%%",properties.tag)
                                    frame = commons.get_image_framing(
                                        properties.attrib, child
                                    )
                                    print("^^^^^^^^^^^^^^^^^^^^^^^^^",frame)
                                    innerStyle += frame

                                if properties.tag == "BlendingSetting":
                                    opacity = commons.BlendingSetting(properties.attrib)
                                    innerStyle += opacity

                                if properties.tag == "Link":
                                    for link in properties.iter():
                                        if link.tag == "Link":
                                            imageUrl = commons.process_image(
                                                link.attrib.get("LinkResourceURI"),
                                                outerStyle,
                                                innerStyle,
                                            )
                                            characterStyle += imageUrl

                        if child.tag == "Properties":
                            for properties in child.iter():
                                print("##child properties",properties)
                                if hasattr(commons, properties.tag):
                                    attr_function = getattr(commons, properties.tag)
                                    characterStyleDict[properties.tag] = attr_function(
                                        properties.text, package, args
                                    )

                                # if properties.tag == "Leading":
                                #     lineHeight = commons.get_line_height(
                                #         properties.text
                                #     )

                                # if properties.tag == "AppliedFont":
                                #     fontFamily = commons.get_font_family(
                                #         properties.text
                                #     )
                        if child.tag == "Content":
                            # characterStyle += "<span "
                            # characterStyle += (
                            #     "style='" + fontStyle + ";" if fontStyle else ""
                            # )
                            # characterStyle += fontColor + ";" if fontColor else ""
                            # characterStyle += strokeColor + ";" if strokeColor else ""
                            # characterStyle += underline + ";" if underline else ""
                            # # characterStyle += strikeThrough + ";" if strikeThrough else ""
                            # characterStyle += fontFamily + ";" if fontFamily else ""
                            # characterStyle += lineHeight + ";" if lineHeight else ""
                            # characterStyle += fontSize + ";" if fontSize else ""
                            # characterStyle += background + ";" if strikeThrough else ""
                            # characterStyle += "'>" + child.text if child.text else "'>"
                            # characterStyle += "</span>"
                            
                            if "FontStyle" in characterStyleDict:
                                if(characterStyleDict.get("FontStyle").find(":")==-1):
                                    characterStyleDict["AppliedFont"] = characterStyleDict["AppliedFont"] + " " +characterStyleDict["FontStyle"]
                                    del characterStyleDict["FontStyle"]

                            # if "StrokeWeight" in characterStyleDict:
                            #     characterStyleDict["StrokeWeight"] = characterStyleDict["StrokeColor"] + " " +characterStyleDict["StrokeWeight"]
                            #     del characterStyleDict["StrokeColor"]       

                            finalCharStyle = "; ".join(
                                list(characterStyleDict.values())
                            )
                            print("---Text---",child.text)
                            characterStyle += f"<span style='{finalCharStyle}'>{child.text if child.text else None }</span>"

                        if child.tag == "Br":
                            characterStyle += "<br />"

                    # Append character style to paragraph style
                    paragraghStyle += characterStyle

                # Close the paragraph style
                paragraghStyle += "</p>"
                htmlContent += paragraghStyle

        return htmlContent

