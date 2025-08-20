import os
import zipfile
import xml.etree.ElementTree as ET
from inspect import cleandoc
import torch
import numpy as np
from PIL import Image, ImageOps
import tempfile
import json
import glob
import shutil


def parse_comic_info(xml_content):
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


class CBZUnpacker:
    """
    This node extracts images and metadata from CBZ (Comic Book Archive) files.
    CBZ files are essentially ZIP archives containing comic book pages as images
    and optional metadata in ComicInfo.xml format.
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

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("IMAGES", "FILENAMES", "METADATA", "CBZ_ID")
    OUTPUT_IS_LIST = (True, True, False, True)
    
    DESCRIPTION = cleandoc(__doc__)
    FUNCTION = "unpack_cbz"
    
    CATEGORY = "image/cbz"

    @classmethod
    def IS_CHANGED(cls, cbz_path, **kwargs):
        if not os.path.exists(cbz_path):
            return "file_not_found"
        return os.path.getmtime(cbz_path)

    def unpack_cbz(self, cbz_path, image_load_cap=0, start_index=0, sort_images=True):
        if not os.path.exists(cbz_path):
            raise FileNotFoundError(f"CBZ file '{cbz_path}' not found.")
        
        if not cbz_path.lower().endswith('.cbz'):
            raise ValueError("File must have .cbz extension.")
        
        images = []
        filenames = []
        
        # Generate unique CBZ identifier
        cbz_id = f"cbz_{hash(cbz_path)}_{os.path.basename(cbz_path)}"
        metadata = "{}"  # Default empty JSON
        
        # Valid image extensions
        valid_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff')
        
        try:
            with zipfile.ZipFile(cbz_path, 'r') as cbz_file:
                # Extract ComicInfo.xml if present
                try:
                    with cbz_file.open('ComicInfo.xml') as comic_info:
                        xml_content = comic_info.read().decode('utf-8')
                        metadata = parse_comic_info(xml_content)
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
                            
                            images.append(image_tensor)
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
        
        # Create CBZ_ID list (same ID for all images from this CBZ)
        cbz_ids = [cbz_id] * len(images)
        
        return (images, filenames, metadata, cbz_ids)

class DirToCBZ:
    """
    Recursively searches through a directory and its subdirectories
    to find all CBZ files and returns their file paths as a list.
    """
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Directory path to search for CBZ files"
                }),
            },
            "optional": {
                "recursive": ("BOOLEAN", {
                    "default": True,
                    "label_on": "enabled",
                    "label_off": "disabled",
                    "tooltip": "Search subdirectories recursively"
                }),
                "sort_paths": ("BOOLEAN", {
                    "default": True,
                    "label_on": "enabled",
                    "label_off": "disabled",
                    "tooltip": "Sort file paths alphabetically"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("CBZ_PATHS",)
    OUTPUT_IS_LIST = (True,)
    
    DESCRIPTION = cleandoc(__doc__)
    FUNCTION = "find_cbz_files"
    
    CATEGORY = "image/cbz"

    @classmethod
    def IS_CHANGED(cls, directory_path, **kwargs):
        """
        Check if directory contents have changed.
        """
        if not os.path.exists(directory_path):
            return "directory_not_found"
        return str(os.path.getmtime(directory_path))

    def find_cbz_files(self, directory_path, recursive=True, sort_paths=True):
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory '{directory_path}' not found.")
        
        if not os.path.isdir(directory_path):
            raise ValueError(f"Path '{directory_path}' is not a directory.")
        
        cbz_files = []
        
        if recursive:
            # Use glob to recursively find CBZ files
            pattern = os.path.join(directory_path, "**", "*.cbz")
            cbz_files = glob.glob(pattern, recursive=True)
        else:
            # Only search in the immediate directory
            pattern = os.path.join(directory_path, "*.cbz")
            cbz_files = glob.glob(pattern)
        
        if sort_paths:
            cbz_files.sort()
        
        if not cbz_files:
            print(f"Warning: No CBZ files found in directory '{directory_path}'")
        
        return (cbz_files,)


class CBZCollector:
    """
    Collects images that have been processed individually
    and groups them back together by their original CBZ file,
    preparing them for export. This allows for arbitrary processing
    nodes to be inserted between Unpacker and Exporter.
    
    The node waits until it has received all images for a CBZ
    before outputting the complete set.
    """
    
    def __init__(self):
        self.image_groups = {}
        self.filename_groups = {}
        self.metadata_cache = {}
        self.expected_counts = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_mode": (["single_images", "batch_list"], {
                    "default": "single_images",
                    "tooltip": "Single images: collect individual images. Batch list: process a complete list as one CBZ."
                }),
            },
            "optional": {
                "images": ("IMAGE", {"tooltip": "Processed images"}),
                "filenames": ("STRING", {"tooltip": "Original filenames"}),
                "metadata": ("STRING", {"tooltip": "CBZ metadata"}),
                "cbz_ids": ("STRING", {"tooltip": "CBZ identifier"}),
                "force_output": ("BOOLEAN", {
                    "default": False,
                    "label_on": "enabled",
                    "label_off": "disabled",
                    "tooltip": "Force output even if collection seems incomplete"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("IMAGES", "FILENAMES", "METADATA", "CBZ_PATH")
    OUTPUT_IS_LIST = (True, True, False, False)
    INPUT_IS_LIST = (False, True, True, False, True)
    
    DESCRIPTION = cleandoc(__doc__)
    FUNCTION = "collect_cbz_data"
    
    CATEGORY = "image/cbz"

    @classmethod  
    def IS_CHANGED(cls, **kwargs):
        # Always re-execute to handle dynamic collection
        return float("NaN")

    def collect_cbz_data(self, input_mode, images=None, filenames=None, metadata=None, cbz_ids=None, force_output=False):
        print(f"CBZCollector: Mode={input_mode}, Images received: {len(images) if images else 0}")
        
        if input_mode == "batch_list":
            # Process a complete list as one CBZ
            if not images or len(images) == 0:
                raise ValueError("No images provided in batch mode")
            
            # Use the first cbz_id for the entire batch
            batch_cbz_id = cbz_ids[0] if cbz_ids and len(cbz_ids) > 0 else "batch_cbz"
            batch_metadata = metadata[0] if metadata and len(metadata) > 0 else "{}"
            
            # Extract original path from CBZ ID
            cbz_path = batch_cbz_id.split('_', 2)[-1] if '_' in batch_cbz_id else f"{batch_cbz_id}.cbz"
            
            print(f"CBZCollector: Processing batch of {len(images)} images as {cbz_path}")
            
            return (images, filenames, batch_metadata, [cbz_path])
        
        else:  # single_images mode
            # Group data by CBZ ID (original behavior)
            if not images or not filenames or not metadata or not cbz_ids:
                raise ValueError("All inputs are required in single_images mode")
            
            for img, fname, meta, cbz_id in zip(images, filenames, metadata, cbz_ids):
                if cbz_id not in self.image_groups:
                    self.image_groups[cbz_id] = []
                    self.filename_groups[cbz_id] = []
                    self.metadata_cache[cbz_id] = meta
                
                self.image_groups[cbz_id].append(img)
                self.filename_groups[cbz_id].append(fname)
            
            # Output complete CBZ groups
            all_images = []
            all_filenames = []
            all_metadata = []
            all_cbz_paths = []
            
            for cbz_id in list(self.image_groups.keys()):
                images_for_cbz = self.image_groups[cbz_id]
                filenames_for_cbz = self.filename_groups[cbz_id]
                metadata_for_cbz = self.metadata_cache[cbz_id]
                
                # Extract original path from CBZ ID
                cbz_path = cbz_id.split('_', 2)[-1] if '_' in cbz_id else f"{cbz_id}.cbz"
                
                print(f"CBZCollector: Outputting {len(images_for_cbz)} images for {cbz_path}")
                
                # Add to output lists
                all_images.extend(images_for_cbz)
                all_filenames.extend(filenames_for_cbz)
                all_metadata.append(metadata_for_cbz)
                all_cbz_paths.append(cbz_path)
                
                # Clear processed group
                del self.image_groups[cbz_id]
                del self.filename_groups[cbz_id]
                del self.metadata_cache[cbz_id]
            
            if not all_images:
                if force_output:
                    print("CBZCollector: Force output enabled but no images collected")
                    return ([], [], "{}", [])
                raise ValueError("No complete CBZ groups ready for output")
            
            return (all_images, all_filenames, all_metadata, all_cbz_paths)


class ExportCBZ:
    """
    A CBZ export node for ComfyUI
    
    This node takes a list of images, filenames, and metadata to create
    a new CBZ (Comic Book Archive) file. It preserves the original structure
    and metadata while allowing for processed images to be saved.
    
    The intended use case is to process images from CBZ Unpacker and
    export them back to a CBZ format with the same structure.
    """
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        """
        Return a dictionary which contains config for all input fields.
        """
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "List of processed images"}),
                "filenames": ("STRING", {"tooltip": "Original filenames from CBZ"}),
                "metadata": ("STRING", {"tooltip": "Metadata JSON string"}),
                "cbz_path": ("STRING", {"tooltip": "Original CBZ path for naming"}),
                "output_directory": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Output directory (leave empty to use same as input)"
                }),
            },
            "optional": {
                "image_quality": ("INT", {
                    "default": 95,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "tooltip": "JPEG quality for exported images (1-100)"
                }),
                "image_format": (["JPEG", "PNG"], {
                    "default": "JPEG",
                    "tooltip": "Output image format"
                }),
                "preserve_structure": ("BOOLEAN", {
                    "default": True,
                    "label_on": "enabled",
                    "label_off": "disabled",
                    "tooltip": "Keep original directory structure and filenames"
                }),
                "suffix": ("STRING", {
                    "default": "_processed",
                    "multiline": False,
                    "tooltip": "Suffix to add to output filename"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("OUTPUT_PATH",)
    OUTPUT_IS_LIST = (False,)
    INPUT_IS_LIST = True  # This node expects all inputs as lists
    
    DESCRIPTION = cleandoc(__doc__)
    FUNCTION = "export_cbz"
    
    CATEGORY = "image/cbz"

    def create_comic_info_xml(self, metadata_json):
        try:
            metadata = json.loads(metadata_json)
            
            # Skip if it's an error or no metadata
            if "error" in metadata or "info" in metadata:
                return None
            
            # Create XML root
            root = ET.Element("ComicInfo")
            
            # Standard fields to include in XML
            xml_fields = [
                'Title', 'Series', 'Number', 'Count', 'Volume', 'AlternateSeries',
                'AlternateNumber', 'StoryTitle', 'Summary', 'Notes', 'Year', 'Month',
                'Day', 'Writer', 'Penciller', 'Inker', 'Colorist', 'Letterer',
                'CoverArtist', 'Editor', 'Publisher', 'Imprint', 'Genre', 'Web',
                'PageCount', 'LanguageISO', 'Format', 'BlackAndWhite', 'Manga',
                'Characters', 'Teams', 'Locations', 'ScanInformation', 'StoryArc',
                'SeriesGroup', 'AgeRating', 'CommunityRating'
            ]
            
            # Add fields to XML
            for field in xml_fields:
                if field in metadata:
                    element = ET.SubElement(root, field)
                    element.text = str(metadata[field])
            
            # Handle Pages if present
            if 'Pages' in metadata and isinstance(metadata['Pages'], list):
                pages_element = ET.SubElement(root, 'Pages')
                for page_info in metadata['Pages']:
                    page_element = ET.SubElement(pages_element, 'Page')
                    for key, value in page_info.items():
                        page_element.set(key, str(value))
            
            return ET.tostring(root, encoding='unicode', xml_declaration=True)
            
        except (json.JSONDecodeError, Exception):
            return None

    def export_cbz(self, images, filenames, metadata, cbz_path, output_directory="", suffix="_processed",
               image_quality=95, image_format="JPEG", preserve_structure=True):
        """
        Export images and metadata to a CBZ file.
        
        Args:
            images: List of image tensors
            filenames: List of original filenames
            metadata: JSON metadata string
            cbz_path: Original CBZ path for reference (now a deeply nested list)
            output_directory: Output directory (empty = same as input)
            suffix: Suffix for output filename
            image_quality: JPEG quality (1-100)
            image_format: Output format ("JPEG" or "PNG")
            preserve_structure: Keep original filenames and structure
            
        Returns:
            tuple: (output_path,)
        """
        # Debug: print the exact structure we're receiving
        print(f"ExportCBZ DEBUG: cbz_path type: {type(cbz_path)}, value: {cbz_path}")
        print(f"ExportCBZ DEBUG: metadata type: {type(metadata)}, value: {metadata}")
        
        # Handle deeply nested cbz_path structure
        def extract_string_from_nested_list(nested_item):
            """Recursively extract string from nested list structure"""
            if isinstance(nested_item, str):
                return nested_item
            elif isinstance(nested_item, list) and nested_item:
                return extract_string_from_nested_list(nested_item[0])
            else:
                # Fallback: use a default name
                return "unknown_cbz"
        
        cbz_path = extract_string_from_nested_list(cbz_path)
        
        # Handle metadata which is also a nested list
        if isinstance(metadata, list) and metadata:
            metadata = extract_string_from_nested_list(metadata)
        
        # Generate output path
        if not output_directory:
            output_directory = os.path.dirname(cbz_path)
        
        base_name = os.path.splitext(os.path.basename(cbz_path))[0]
        output_filename = f"{base_name}{suffix}.cbz"
        output_path = os.path.join(output_directory, output_filename)
        
        # Ensure output directory exists
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Handle the case where inputs might be lists or single items
        if not isinstance(images, list):
            images = [images]
        if not isinstance(filenames, list):
            filenames = [filenames]
        
        print(f"ExportCBZ: Processing {len(images)} images for {output_path}")
        print(f"ExportCBZ: Final cbz_path: {cbz_path}")
        
        if len(images) != len(filenames):
            raise ValueError(f"Number of images ({len(images)}) must match number of filenames ({len(filenames)})")
        
        # Create temporary directory for CBZ contents
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save images
            for i, (image_tensor, original_filename) in enumerate(zip(images, filenames)):
                # Convert tensor back to PIL Image
                # Remove batch dimension and convert to numpy
                image_np = image_tensor.squeeze(0).numpy()
                # Convert from float [0,1] to uint8 [0,255]
                image_np = (image_np * 255).astype(np.uint8)
                pil_image = Image.fromarray(image_np, 'RGB')
                
                # Determine output filename
                if preserve_structure and original_filename:
                    # Use original filename but change extension if needed
                    base_name = os.path.splitext(original_filename)[0]
                    if image_format == "PNG":
                        output_filename = f"{base_name}.png"
                    else:
                        output_filename = f"{base_name}.jpg"
                else:
                    # Generate sequential filename
                    if image_format == "PNG":
                        output_filename = f"page_{i+1:04d}.png"
                    else:
                        output_filename = f"page_{i+1:04d}.jpg"
                
                # Create subdirectories if needed
                full_path = os.path.join(temp_dir, output_filename)
                subdir = os.path.dirname(full_path)
                if subdir and not os.path.exists(subdir):
                    os.makedirs(subdir)
                
                # Save image
                if image_format == "PNG":
                    pil_image.save(full_path, "PNG", optimize=True)
                else:
                    pil_image.save(full_path, "JPEG", quality=image_quality, optimize=True)
            
            # Create ComicInfo.xml if we have metadata
            comic_info_xml = self.create_comic_info_xml(metadata)
            if comic_info_xml:
                comic_info_path = os.path.join(temp_dir, "ComicInfo.xml")
                with open(comic_info_path, 'w', encoding='utf-8') as f:
                    f.write(comic_info_xml)
            
            # Create CBZ file (which is just a ZIP file)
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as cbz_file:
                # Add all files from temp directory
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Calculate relative path from temp_dir
                        arc_name = os.path.relpath(file_path, temp_dir)
                        cbz_file.write(file_path, arc_name)
        
        return (output_path,)

# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "CBZUnpacker": CBZUnpacker,
    "DirToCBZ": DirToCBZ,
    "CBZCollector": CBZCollector,
    "ExportCBZ": ExportCBZ,

}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "CBZUnpacker": "CBZ Unpacker",
    "DirToCBZ": "Directory to CBZ List", 
    "CBZCollector": "CBZ Collector",
    "ExportCBZ": "Export CBZ",
}