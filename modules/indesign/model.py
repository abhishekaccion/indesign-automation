import xml.etree.ElementTree as ET

import modules.lib.commons as commons
from ast import literal_eval
import re

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
        stories = []

        for spread in package.spreads:
            tree = ET.parse(args.extract + spread)
            root = tree.getroot()

            # page = self.setup_page(root)
            # self.get_transformations(root, page)
            for story_iterator in root.iter():
                if story_iterator.tag == "TextFrame":
                    story = story_iterator.get("ParentStory")
                    if story not in stories:
                        stories.append(story)
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

        htmlContent = "<style>p { margin: 0px;} ul { margin: 0px}</style>"

        paragraphStyleRangeLength = 0
        for paragraphStyleRange in root.iter("ParagraphStyleRange"):
            paragraphStyleRangeLength +=1
        paragraphStyleRangeCounter = 0
        for paragraphStyleRange in root.iter("ParagraphStyleRange"):
            paragraphStyleRangeCounter +=1
            paragraphStyleList = {}

            for paragraph_attr in paragraphStyleRange.attrib:
                print("##paragraph_attr : ",paragraph_attr,paragraphStyleRange.attrib.get(paragraph_attr))
                if hasattr(commons, paragraph_attr):
                    attr_function = getattr(commons, paragraph_attr)
                    paragraphStyleList[paragraph_attr] = attr_function(
                        paragraphStyleRange.attrib.get(paragraph_attr), package, args
                    )

            paraStyle = "; ".join(list(paragraphStyleList.values()))
            listItemParagraph = paragraphStyleRange.attrib.get(
                "BulletsAndNumberingListType"
            )
            if listItemParagraph:
                    
                listItem=""
                listItem += f"<li>"
                
                for characterStyleRange in paragraphStyleRange.iter(
                    "CharacterStyleRange"
                ):
                   
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
                    lineStyle = "; ".join(list(characterStyleDict.values()))
                    print("###LI characterStyleRange : ",characterStyleRange.attrib )
                    
                    for child in characterStyleRange.iter():
                        print("###LI Child Text",child.attrib)
                        if child.tag == "Content":
                            listItem += f"<span style='{lineStyle}'>{child.text}</span>"
                            print("---Text-LI--",child.text)
                        if child.tag == "Br":
                            listItem += f"</li><li>"
                    if "LeftIndent" in paragraphStyleList:
                        if "FirstLineIndent" in paragraphStyleList:
                            del paragraphStyleList["FirstLineIndent"]
                        paragraphStyleList["LeftIndent"] = f" padding-inline-start "+ paragraphStyleList.get("LeftIndent")[paragraphStyleList.get("LeftIndent").find(":"):]
                        paraStyle = "; ".join(list(paragraphStyleList.values()))
                
                if listItemParagraph == "NumberedList" and listItem !="":
                    htmlContent += f"<ol style='{paraStyle}'>{listItem}</ol><br>"        
                elif listItem !="":
                    htmlContent += f"<ul style='{paraStyle}'>{listItem}</ul>"
                    htmlContent = htmlContent.replace("</p><br><ul","</p><ul").replace("<li></ul>","</ul>")
            else:
                paragraghStyle = f"<p style='{paraStyle}'>"
                characterStyleRangeLength = 0
                for characterStyleRange in paragraphStyleRange.iter(
                    "CharacterStyleRange"
                ):
                    characterStyleRangeLength +=1
                
                #counter 
                characterStyleRangeCounter = 0
                for characterStyleRange in paragraphStyleRange.iter(
                    "CharacterStyleRange"
                ):
                    characterStyleRangeCounter +=1
                    # print("### characterStyleRange : ",characterStyleRange,characterStyleRange.attrib )
                    characterStyle = ""
                    characterStyleDict = {
                        "FontStyle": "font-weight: normal",
                        "FillColor": "color:rgb(0, 0, 0)",
                        "AppliedFont": commons.AppliedFont(None),
                        "Leading": commons.Leading(None),
                        "PointSize": "font-size: 12pt",
                    }

                    for char_attr in characterStyleRange.attrib:
                        # print("##char attr :  ",char_attr,characterStyleRange.attrib.get(char_attr))
                        if hasattr(commons, char_attr):
                            attr_function = getattr(commons, char_attr)
                            characterStyleDict[char_attr] = attr_function(
                                characterStyleRange.attrib.get(char_attr), package, args
                            )

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

                    # Get the Image url
                    imageUrl = ""
                    second_last_tag = ""
                    last_tag = ""
                    
                    characterStyleRangeChildLength = 0
                    for child in characterStyleRange.iter():
                        characterStyleRangeChildLength +=1

                    #counter
                    characterStyleRangeChildCounter = 0
                    for child in characterStyleRange.iter():
                        characterStyleRangeChildCounter +=1
                        # print("******************",paragraphStyleRangeLength,paragraphStyleRangeCounter,characterStyleRangeLength,characterStyleRangeCounter,characterStyleRangeChildLength,characterStyleRangeChildCounter,last_tag,child.tag)
                        print("##child properties",child.attrib)
                        if child.tag == "Rectangle":
                            outerStyle = "display: inline-block; overflow:hidden;"
                            innerStyle = ""

                            border_radius = commons.get_image_border_radius(
                                child.attrib
                            )
                            outerStyle += border_radius
                            for properties in child.iter():
                                # print("------child props------",properties,properties.attrib)
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
                                        properties.attrib, child
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
                                            characterStyle += imageUrl

                        if child.tag == "Properties":
                            for properties in child.iter():
                                
                                if hasattr(commons, properties.tag):
                                    attr_function = getattr(commons, properties.tag)
                                    characterStyleDict[properties.tag] = attr_function(
                                        properties.text, package, args
                                    )

                        if child.tag == "Content":
                            
                            if "FontStyle" in characterStyleDict:
                                if(characterStyleDict.get("FontStyle").find(":")==-1):
                                    characterStyleDict["AppliedFont"] = characterStyleDict["AppliedFont"] + " " +characterStyleDict["FontStyle"]
                                    del characterStyleDict["FontStyle"]

                            finalCharStyle = "; ".join(
                                list(characterStyleDict.values())
                            )
                            print("---Text-P--",child.text)
                            characterStyle += f"<span style='{finalCharStyle}'>{child.text if child.text else None }</span>"

                        if child.tag == "Br":
                            # print("------------",characterStyleRangeLength,characterStyleRangeCounter,second_last_tag,last_tag,child.tag)
                            if characterStyleRangeLength == characterStyleRangeCounter and characterStyleRangeChildLength == characterStyleRangeChildCounter and last_tag == "Br" :
                                pass
                            # elif characterStyleRangeLength == characterStyleRangeCounter and last_tag == "Content" :
                            #     pass    
                            elif characterStyleRangeLength == 1 and last_tag == "CharacterStyleRange" :
                                pass   
                            elif characterStyleRangeCounter == 1 and last_tag == "AppliedFont" :
                                pass
                            # elif characterStyleRangeCounter != characterStyleRangeLength and characterStyleRangeChildCounter == 4 :
                            #     pass    
                            elif last_tag == "Br":
                                characterStyle += f"</p><p style='margin: 0px;{paraStyle}'>"
                            elif last_tag == "Content":
                                characterStyle += "<br>"
                            elif last_tag == "CharacterStyleRange":
                                characterStyle += "<br>"   
                            elif last_tag == "AppliedFont":
                                characterStyle += "<br>" 
                            elif last_tag == "Leading":
                                characterStyle += "<br>"         

                        #update last_tag
                        second_last_tag = last_tag
                        last_tag = child.tag        

                    # Append character style to paragraph style
                    paragraghStyle += characterStyle

                # Close the paragraph style
                paragraghStyle += "</p>"
                pattern = re.compile(r"<p([^>]*)><\/p>")
                # paragraghStyle = paragraghStyle.replace("<p style=''><br></p>","<br>")
                # paragraghStyle = paragraghStyle.replace("<p style=''><br></p>","")
                # paragraghStyle = paragraghStyle.replace("<br></p>","</p>")
                # paragraghStyle = paragraghStyle.replace("</span><br><span","</span><br><br><span")
                # if paragraghStyle.find("<br></p>") == -1:
                #     paragraghStyle = paragraghStyle.replace("</p>","<br></p>")
                   
                # paragraghStyle = pattern.sub("",paragraghStyle)
                
                htmlContent += paragraghStyle

        return htmlContent

