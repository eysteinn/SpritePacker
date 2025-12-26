# SpritePacker

Lightweight sprite atlas packer implemented with the MaxRects heuristic. Supports multiple pages, JSON/YAML metadata export, and folder batch processing.

## Features
- **MaxRects packing** - Efficient rectangle packing algorithm
- **Multi-page support** - Automatically creates multiple atlas pages when needed
- **Padding & extrude** - Prevents texture bleeding with configurable padding and edge pixel extrusion
- **Flexible metadata** - Export sprite coordinates as JSON or YAML
- **Batch processing** - Add entire folders of images with one call
- **Customizable** - Pluggable algorithm, multiple image modes (RGBA, RGB, LA, etc.)

## Usage

```python
from SpritePacker import SpritePacker

# Create packer with 1024x1024 atlas pages
# mode defaults to "RGBA"; change if you need RGB, LA, etc.
# max_pages=None means unlimited; set an int to cap page allocation.
# extrude=True repeats border pixels into the padding area to prevent bleeding.
packer = SpritePacker(1024, 1024, padding=2, mode="RGBA", max_pages=None, extrude=True)

# Add individual images
packer.add_image("hero_idle", "assets/hero_idle.png")
packer.add_image("hero_run", "assets/hero_run.png")

# Or add entire folders
packer.add_folder("assets/sprites", recursive=True, strip_folder_path=True)

# Save atlas images (creates atlas.png or atlas_0.png, atlas_1.png, ...)
paths = packer.save_atlas("atlas.png")
print(paths)

# Save metadata as JSON or YAML (auto-detected by extension)
packer.save_metadata("atlas.json")  # JSON format
packer.save_metadata("atlas.yaml")  # YAML format

# Or get metadata as dict
print(packer.get_metadata())  # includes page index per sprite
```

## API Reference

### SpritePacker

**Constructor:**
```python
SpritePacker(width, height, *, padding=1, background=(0,0,0,0), mode="RGBA", 
             max_pages=None, algorithm=None, extrude=False)
```
- `width`, `height`: Atlas page dimensions
- `padding`: Pixels between sprites (default: 1)
- `background`: Background color as RGBA tuple (default: transparent)
- `mode`: PIL image mode (default: "RGBA")
- `max_pages`: Maximum number of pages (default: unlimited)
- `algorithm`: Custom packing algorithm (default: MaxRectsAlgorithm)
- `extrude`: Repeat edge pixels into padding to prevent bleeding (default: False)
  - **Note:** Requires `padding > 0` or raises `ValueError`

**Methods:**
- `add_image(name, image)` - Add a single image (returns Rect)
  - `name`: Sprite identifier (will be converted to string)
  - `image`: File path (str/Path) or PIL.Image object
  
- `add_folder(folder, recursive=False, extensions={".png",".jpg",".jpeg"}, strip_folder_path=True)` - Add all images from folder
  - `folder`: Path to folder
  - `recursive`: Search subdirectories
  - `extensions`: File extensions to include
  - `strip_folder_path`: Use relative paths as names (default: True)

- `save_atlas(path)` - Save atlas images, returns list of saved paths
  - Use `{page}` in filename for custom multi-page naming
  
- `save_metadata(path)` - Save sprite metadata (JSON/YAML auto-detected by extension)
  - `.json` extension → JSON format
  - Any other extension → YAML format

- `get_metadata()` - Returns dict with sprite positions and page indices

- `atlas_images()` - Returns list of PIL.Image objects (one per page)

## Metadata Format

Both JSON and YAML exports follow this structure:
```yaml
atlas:
  width: 1024
  height: 1024
  pages: 2
pages:
  - atlas_0.png
  - atlas_1.png
sprites:
  hero_idle.png:
    x: 10
    y: 10
    width: 64
    height: 64
    page: 0
  hero_run.png:
    x: 76
    y: 10
    width: 64
    height: 64
    page: 0
```

## Installation

Requires Pillow and PyYAML:
```bash
pip install Pillow PyYAML
```

## Notes
- Automatically allocates new pages when a sprite doesn't fit in existing pages
- Names can be strings or Path objects (automatically converted to strings)
- Padding is required for `extrude` mode - raises `ValueError` if `extrude=True` and `padding=0`
- Uses a pluggable packing algorithm; defaults to MaxRects
