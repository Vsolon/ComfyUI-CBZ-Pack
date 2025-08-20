import json
import xml.etree.ElementTree as ET



def parse_comic_info(self, xml_content):
        try:
            root = ET.fromstring(xml_content)
            metadata = {}
            
            # Common ComicInfo.xml fields
            fields = [
                'Title', 'Series', 'Number', 'Count', 'Volume', 'AlternateSeries',
                'AlternateNumber', 'StoryTitle', 'Summary', 'Notes', 'Year', 'Month',
                'Day', 'Writer', 'Penciller', 'Inker', 'Colorist', 'Letterer',
                'CoverArtist', 'Editor', 'Publisher', 'Imprint', 'Genre', 'Web',
                'PageCount', 'LanguageISO', 'Format', 'BlackAndWhite', 'Manga',
                'Characters', 'Teams', 'Locations', 'ScanInformation', 'StoryArc',
                'SeriesGroup', 'AgeRating', 'CommunityRating'
            ]
            
            for field in fields:
                element = root.find(field)
                if element is not None and element.text:
                    metadata[field] = element.text
            
            # Handle Pages element if present
            pages_element = root.find('Pages')
            if pages_element is not None:
                pages = []
                for page in pages_element.findall('Page'):
                    page_info = {}
                    for attr in ['Image', 'Type', 'DoublePage', 'ImageSize', 'Key']:
                        if attr in page.attrib:
                            page_info[attr] = page.attrib[attr]
                    if page_info:
                        pages.append(page_info)
                if pages:
                    metadata['Pages'] = pages
            
            return json.dumps(metadata, indent=2)
            
        except ET.ParseError as e:
            return json.dumps({"error": f"Failed to parse ComicInfo.xml: {str(e)}"}, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Error processing metadata: {str(e)}"}, indent=2)