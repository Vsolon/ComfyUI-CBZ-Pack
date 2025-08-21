from inspect import cleandoc

# Global variable for preview (as shown in the example)
_curr_preview = {}

def show_text(text: str):
    """Add a preview text to the ComfyUI node.
    
    Args:
        text (str): The text to display.
    """
    if "text" not in _curr_preview:
        _curr_preview["text"] = []
    _curr_preview["text"].append(text)


class DirToCBZPassthrough:    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "cbz_paths": ("STRING", {"tooltip": "CBZ paths from DirToCBZ"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("CBZ_PATHS",)
    OUTPUT_IS_LIST = (True,)
    INPUT_IS_LIST = (True,)
    OUTPUT_NODE = True
    FUNCTION = "passthrough"
    CATEGORY = "image/cbz/debug"

    def passthrough(self, cbz_paths):
        print(f"DirToCBZPassthrough: Received {len(cbz_paths)} CBZ paths")
        
        # Create display text with all paths
        display_text = f"Found {len(cbz_paths)} CBZ files:\n\n"
        for i, path in enumerate(cbz_paths):
            display_text += f"{i+1}. {path}\n"
            print(f"  [{i}]: {path}")
        
        # Use the show_text function to display in UI
        show_text(display_text)
        
        # Return the result for downstream nodes
        result = (cbz_paths,)
        
        # Combine with the preview data
        if _curr_preview:
            return {"ui": _curr_preview, "result": result}
        else:
            return {"result": result}


# Display-only node
class CBZPathDisplay:
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "cbz_paths": ("STRING", {"tooltip": "CBZ paths to display"}),
            }
        }

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "display"
    CATEGORY = "image/cbz/debug"

    def display(self, cbz_paths):
        print(f"CBZPathDisplay: Received {len(cbz_paths)} CBZ paths")
        
        # Create display text with all paths
        display_text = f"Found {len(cbz_paths)} CBZ files:\n\n"
        for i, path in enumerate(cbz_paths):
            display_text += f"{i+1}. {path}\n"
            print(f"  [{i}]: {path}")
        
        # Use the show_text function to display in UI
        show_text(display_text)
        
        # Return only the UI data for output nodes
        return {"ui": _curr_preview}

class CBZUnpackerPassthrough: 
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "Images from CBZUnpacker"}),
                "filenames": ("STRING", {"tooltip": "Filenames from CBZUnpacker"}),
                "metadata": ("STRING", {"tooltip": "Metadata from CBZUnpacker"}),
                "cbz_ids": ("STRING", {"tooltip": "CBZ IDs from CBZUnpacker"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("IMAGES", "FILENAMES", "METADATA", "CBZ_IDS")
    OUTPUT_IS_LIST = (True, True, False, True)
    INPUT_IS_LIST = (True, True, False, True)
    
    FUNCTION = "passthrough"
    CATEGORY = "image/cbz/debug"

    def passthrough(self, images, filenames, metadata, cbz_ids):
        print(f"CBZUnpackerPassthrough: Received {len(images)} images")
        print(f"  CBZ IDs: {len(cbz_ids)} unique IDs")
        print(f"  Metadata: {metadata[:100]}...")  # First 100 chars
        
        unique_ids = set(cbz_ids)
        for cbz_id in unique_ids:
            count = cbz_ids.count(cbz_id)
            print(f"  ID '{cbz_id}': {count} images")
            
        return (images, filenames, metadata, cbz_ids)

class CBZCollectorPassthrough:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "Images from CBZCollector"}),
                "filenames": ("STRING", {"tooltip": "Filenames from CBZCollector"}),
                "metadata": ("STRING", {"tooltip": "Metadata from CBZCollector"}),
                "cbz_paths": ("STRING", {"tooltip": "CBZ paths from CBZCollector"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("IMAGES", "FILENAMES", "METADATA", "CBZ_PATHS")
    OUTPUT_IS_LIST = (True, True, False, False)
    INPUT_IS_LIST = (True, True, False, False)
    
    FUNCTION = "passthrough"
    CATEGORY = "image/cbz/debug"

    def passthrough(self, images, filenames, metadata, cbz_paths):
        print(f"CBZCollectorPassthrough: Received {len(images)} images")
        print(f"  CBZ paths: {cbz_paths}")
        print(f"  Metadata type: {type(metadata)}")
        
        if isinstance(cbz_paths, list):
            print(f"  Number of CBZ paths: {len(cbz_paths)}")
            for i, path in enumerate(cbz_paths):
                print(f"    [{i}]: {path}")
        else:
            print(f"  Single CBZ path: {cbz_paths}")
            
        return (images, filenames, metadata, cbz_paths)

class ExportCBZPassthrough:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "output_path": ("STRING", {"tooltip": "Output path from ExportCBZ"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("OUTPUT_PATH",)
    OUTPUT_IS_LIST = (False,)
    INPUT_IS_LIST = (False,)
    
    FUNCTION = "passthrough"
    CATEGORY = "image/cbz/debug"

    def passthrough(self, output_path):
        print(f"ExportCBZPassthrough: Output path = {output_path}")
        return (output_path,)

# Add to your node mappings
NODE_CLASS_MAPPINGS = { 
    "DirToCBZPassthrough": DirToCBZPassthrough,
    "CBZUnpackerPassthrough": CBZUnpackerPassthrough,
    "CBZCollectorPassthrough": CBZCollectorPassthrough,
    "ExportCBZPassthrough": ExportCBZPassthrough,
    "CBZPathDisplay": CBZPathDisplay
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DirToCBZPassthrough": "DirToCBZ Passthrough (Debug)",
    "CBZUnpackerPassthrough": "CBZUnpacker Passthrough (Debug)",
    "CBZCollectorPassthrough": "CBZCollector Passthrough (Debug)",
    "ExportCBZPassthrough": "ExportCBZ Passthrough (Debug)",
    "CBZPathDisplay": "CBZ Path Display"
}