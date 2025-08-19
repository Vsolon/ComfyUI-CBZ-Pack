import os
import zipfile
import xml.etree.ElementTree as ET
from inspect import cleandoc
import torch
import numpy as np
from PIL import Image, ImageOps
import tempfile
import json

class CBZUnpacker:
    """
    A CBZ unpacker node for ComfyUI
    
    This node extracts images and metadata from CBZ (Comic Book Archive) files.
    CBZ files are essentially ZIP archives containing comic book pages as images
    and optional metadata in ComicInfo.xml format.

    Class methods
    -------------
    INPUT_TYPES (dict):
        Tell the main program input parameters of nodes.
    IS_CHANGED:
        Optional method to control when the node is re executed.

    Attributes
    ----------
    RETURN_TYPES (`tuple`):
        The type of each element in the output tuple.
    RETURN_NAMES (`tuple`):
        The name of each output in the output tuple.
    FUNCTION (`str`):
        The name of the entry-point method.
    OUTPUT_NODE ([`bool`]):
        If this node is an output node that outputs a result/image from the graph.
    CATEGORY (`str`):
        The category the node should appear in the UI.
    """
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        """
        Return a dictionary which contains config for all input fields.
        
        Returns: `dict`:
            Configuration for input fields including CBZ file path and options.
        """
        return {
            "required": {
                "cbz_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Path to the CBZ file to extract"
                }),
            },
            "optional": {
                "image_load_cap": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "step": 1,
                    "tooltip": "Maximum number of images to load (0 = no limit)"
                }),
                "start_index": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "max": 0xffffffffffffffff, 
                    "step": 1,
                    "tooltip": "Start loading from this image index"
                }),
                "sort_images": ("BOOLEAN", {
                    "default": True, 
                    "label_on": "enabled", 
                    "label_off": "disabled",
                    "tooltip": "Sort images by filename"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING")
    RETURN_NAMES = ("IMAGES", "MASKS", "FILENAMES", "METADATA")
    OUTPUT_IS_LIST = (True, True, True, False)
    
    DESCRIPTION = cleandoc(__doc__)
    FUNCTION = "unpack_cbz"
    
    CATEGORY = "image/cbz"

    @classmethod
    def IS_CHANGED(cls, cbz_path, **kwargs):
        """
        Check if the CBZ file has changed by comparing modification time.
        """
        if not os.path.exists(cbz_path):
            return "file_not_found"
        return os.path.getmtime(cbz_path)

    def parse_comic_info(self, xml_content):
        """
        Parse ComicInfo.xml content and return metadata as JSON string.
        
        Args:
            xml_content (str): Raw XML content from ComicInfo.xml
            
        Returns:
            str: JSON formatted metadata
        """
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

    def unpack_cbz(self, cbz_path, image_load_cap=0, start_index=0, sort_images=True):
        """
        Extract images and metadata from CBZ file.
        
        Args:
            cbz_path (str): Path to the CBZ file
            image_load_cap (int): Maximum number of images to load (0 = no limit)
            start_index (int): Start loading from this image index
            sort_images (bool): Whether to sort images by filename
            
        Returns:
            tuple: (images, masks, filenames, metadata)
        """
        if not os.path.exists(cbz_path):
            raise FileNotFoundError(f"CBZ file '{cbz_path}' not found.")
        
        if not cbz_path.lower().endswith('.cbz'):
            raise ValueError("File must have .cbz extension.")
        
        images = []
        masks = []
        filenames = []
        metadata = "{}"  # Default empty JSON
        
        # Valid image extensions
        valid_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff')
        
        try:
            with zipfile.ZipFile(cbz_path, 'r') as cbz_file:
                # Extract ComicInfo.xml if present
                try:
                    with cbz_file.open('ComicInfo.xml') as comic_info:
                        xml_content = comic_info.read().decode('utf-8')
                        metadata = self.parse_comic_info(xml_content)
                except KeyError:
                    # ComicInfo.xml not found, use default metadata
                    metadata = json.dumps({
                        "info": "No ComicInfo.xml found in CBZ file",
                        "filename": os.path.basename(cbz_path)
                    }, indent=2)
                
                # Get list of image files in the archive
                image_files = [f for f in cbz_file.namelist() 
                              if f.lower().endswith(valid_extensions) and not f.startswith('__MACOSX/')]
                
                if not image_files:
                    raise ValueError("No valid image files found in CBZ archive.")
                
                # Sort images if requested
                if sort_images:
                    image_files.sort()
                
                # Apply start_index
                image_files = image_files[start_index:]
                
                # Apply image load cap
                if image_load_cap > 0:
                    image_files = image_files[:image_load_cap]
                
                # Process each image
                for image_file in image_files:
                    try:
                        # Extract image data
                        with cbz_file.open(image_file) as img_data:
                            # Create temporary file to load with PIL
                            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_file)[1]) as temp_file:
                                temp_file.write(img_data.read())
                                temp_path = temp_file.name
                        
                        # Load and process image
                        try:
                            pil_image = Image.open(temp_path)
                            pil_image = ImageOps.exif_transpose(pil_image)
                            
                            # Convert to RGB
                            rgb_image = pil_image.convert("RGB")
                            image_array = np.array(rgb_image).astype(np.float32) / 255.0
                            image_tensor = torch.from_numpy(image_array)[None,]
                            
                            # Handle alpha channel for mask
                            if 'A' in pil_image.getbands():
                                mask_array = np.array(pil_image.getchannel('A')).astype(np.float32) / 255.0
                                mask_tensor = 1. - torch.from_numpy(mask_array)
                            else:
                                # Create empty mask if no alpha channel
                                mask_tensor = torch.zeros((rgb_image.height, rgb_image.width), dtype=torch.float32, device="cpu")
                            
                            images.append(image_tensor)
                            masks.append(mask_tensor)
                            filenames.append(image_file)
                            
                        finally:
                            # Clean up temporary file
                            try:
                                os.unlink(temp_path)
                            except:
                                pass
                                
                    except Exception as e:
                        print(f"Warning: Failed to process image {image_file}: {str(e)}")
                        continue
        
        except zipfile.BadZipFile:
            raise ValueError("Invalid CBZ file: not a valid ZIP archive.")
        except Exception as e:
            raise RuntimeError(f"Error processing CBZ file: {str(e)}")
        
        if not images:
            raise ValueError("No images could be loaded from the CBZ file.")
        
        return (images, masks, filenames, metadata)


# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "CBZUnpacker": CBZUnpacker
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "CBZUnpacker": "CBZ Unpacker"
}