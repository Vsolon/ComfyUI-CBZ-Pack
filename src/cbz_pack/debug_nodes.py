from inspect import cleandoc

class CBZPreviewAny:
    """Display any data as string, for CBZ pipeline debugging/previewing."""

    NAME = "CBZ Preview Any"
    CATEGORY = "CBZ Preview"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "source": ("*", {}),  # Accepts any input type
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "main"
    OUTPUT_NODE = True

    def main(self, source=None, unique_id=None, extra_pnginfo=None):
        value = "None"
        if isinstance(source, str):
            value = source
        elif isinstance(source, (int, float, bool)):
            value = str(source)
        elif source is not None:
            try:
                value = json.dumps(source)
            except Exception:
                try:
                    value = str(source)
                except Exception:
                    value = "source exists, but could not be serialized."

        # Pre-fill on reload
        if extra_pnginfo and unique_id:
            for node in extra_pnginfo.get("workflow", {}).get("nodes", []):
                if str(node.get("id")) == str(unique_id):
                    node["widgets_values"] = [value]
                    break

        return {"ui": {"text": (value,)}}

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
        
        # Return both the paths for downstream nodes and UI display
        return {
            "ui": {"text": (display_text,)},
            "result": (cbz_paths,)
        }

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

NODE_CLASS_MAPPINGS = { 
    "DirToCBZPassthrough": DirToCBZPassthrough,
    "CBZUnpackerPassthrough": CBZUnpackerPassthrough,
    "CBZCollectorPassthrough": CBZCollectorPassthrough,
    "ExportCBZPassthrough": ExportCBZPassthrough,
    "CBZ Preview Any": CBZPreviewAny,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DirToCBZPassthrough": "DirToCBZ Passthrough (Debug)",
    "CBZUnpackerPassthrough": "CBZUnpacker Passthrough (Debug)",
    "CBZCollectorPassthrough": "CBZCollector Passthrough (Debug)",
    "ExportCBZPassthrough": "ExportCBZ Passthrough (Debug)",
     "CBZ Preview Any": "CBZ Preview Any",
}