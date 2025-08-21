from inspect import cleandoc

class DirToCBZPassthrough:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "cbz_paths": ("STRING", {"tooltip": "CBZ paths from DirToCBZ"}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    INPUT_IS_LIST = True
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("CBZ_PATHS",)
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "passthrough"
    CATEGORY = "image/cbz/debug"

    def passthrough(self, cbz_paths, unique_id=None, extra_pnginfo=None):
        print(f"DirToCBZPassthrough: Received {len(cbz_paths)} CBZ paths")
        
        # Create display text with all paths
        display_text = f"Found {len(cbz_paths)} CBZ files:\n\n"
        for i, path in enumerate(cbz_paths):
            display_text += f"{i+1}. {path}\n"
            print(f"  [{i}]: {path}")
        
        # Update node widget values for display (like ShowText does)
        if unique_id is not None and extra_pnginfo is not None:
            if not isinstance(extra_pnginfo, list):
                print("Error: extra_pnginfo is not a list")
            elif (
                not isinstance(extra_pnginfo[0], dict)
                or "workflow" not in extra_pnginfo[0]
            ):
                print("Error: extra_pnginfo[0] is not a dict or missing 'workflow' key")
            else:
                workflow = extra_pnginfo[0]["workflow"]
                node = next(
                    (x for x in workflow["nodes"] if str(x["id"]) == str(unique_id[0])),
                    None,
                )
                if node:
                    node["widgets_values"] = [display_text]
        
        # Return both the UI text and the original paths
        return {"ui": {"text": [display_text]}, "result": (cbz_paths,)}


# Also create a dedicated display node like ShowText
class CBZPathDisplay:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "cbz_paths": ("STRING", {"tooltip": "CBZ paths to display", "forceInput": True}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    INPUT_IS_LIST = True
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "display"
    CATEGORY = "image/cbz/debug"

    def display(self, cbz_paths, unique_id=None, extra_pnginfo=None):
        print(f"CBZPathDisplay: Received {len(cbz_paths)} CBZ paths")
        
        # Create display text with all paths
        display_text = f"Found {len(cbz_paths)} CBZ files:\n\n"
        for i, path in enumerate(cbz_paths):
            display_text += f"{i+1}. {path}\n"
            print(f"  [{i}]: {path}")
        
        # Update node widget values for display (like ShowText does)
        if unique_id is not None and extra_pnginfo is not None:
            if not isinstance(extra_pnginfo, list):
                print("Error: extra_pnginfo is not a list")
            elif (
                not isinstance(extra_pnginfo[0], dict)
                or "workflow" not in extra_pnginfo[0]
            ):
                print("Error: extra_pnginfo[0] is not a dict or missing 'workflow' key")
            else:
                workflow = extra_pnginfo[0]["workflow"]
                node = next(
                    (x for x in workflow["nodes"] if str(x["id"]) == str(unique_id[0])),
                    None,
                )
                if node:
                    node["widgets_values"] = [display_text]
        
        # Return only UI text (no data output)
        return {"ui": {"text": [display_text]}}


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