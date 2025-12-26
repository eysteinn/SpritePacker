from __future__ import annotations

import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Union

from PIL import Image

from .algorithms import MaxRectsAlgorithm, Rect


Color = Tuple[int, int, int, int]


class SpritePacker:
    """Sprite atlas packer with pluggable packing algorithm."""

    def __init__(
        self,
        width: int,
        height: int,
        *,
        padding: int = 1,
        background: Color = (0, 0, 0, 0),
        mode: str = "RGBA",
        max_pages: int = None,
        algorithm=None,
        extrude: bool = False,
    ) -> None:
        self.width = width
        self.height = height
        self.padding = max(0, padding)
        self.background = background
        self.mode = mode
        self.extrude = extrude
        
        if self.extrude and self.padding <= 0:
            raise ValueError("extrude requires padding > 0")
        
        self._atlases: List[Image.Image] = [self._new_page_image()]
        self._algorithm = algorithm or MaxRectsAlgorithm(width, height, max_pages=max_pages)
        self._placements: Dict[str, Tuple[int, Rect]] = {}

    def add_folder(self, folder: Union[str, Path], recursive: bool = False, extensions: set = {".png", ".jpg", ".jpeg"}, strip_folder_path: bool = True) -> None:
        """
        Add all images from a folder to the atlas.
        
        Args:
            folder: Path to the folder containing images
            recursive: If True, search subdirectories
            extensions: Set of file extensions to include
            strip_folder_path: If True, use relative path from folder as name; if False, use full path
        """
        folder_path = Path(folder)
        for entry in folder_path.rglob("*") if recursive else folder_path.iterdir():
            if entry.is_file() and entry.suffix.lower() in extensions:
                name = str(entry.relative_to(folder_path)) if strip_folder_path else str(entry)
                self.add_image(name, entry)


    # Public API -------------------------------------------------------------
    def add_image(self, name: str, image: Union[str, Path, Image.Image]) -> Rect:
        """
        Add an image to the atlas pages. Image can be a file path or a PIL Image.
        Returns the placed rectangle (x, y, width, height) within its page.
        Raises ValueError if the image cannot be placed on any page.
        """
        # Ensure name is always a string (in case a Path is passed)
        name = str(name)
        
        if name in self._placements:
            raise ValueError(f"Sprite '{name}' already added")

        pil_image = self._ensure_image(image)
        padded_w = pil_image.width + self.padding * 2
        padded_h = pil_image.height + self.padding * 2

        page_index, placement = self._algorithm.add(padded_w, padded_h)
        self._ensure_atlas_page(page_index)
        draw_x = placement.x + self.padding
        draw_y = placement.y + self.padding
        self._atlases[page_index].paste(pil_image, (draw_x, draw_y), pil_image)
        if self.extrude and self.padding > 0:
            self._apply_extrude(self._atlases[page_index], pil_image, draw_x, draw_y)
        placed_rect = Rect(draw_x, draw_y, pil_image.width, pil_image.height)
        self._placements[name] = (page_index, placed_rect)
        return placed_rect

    def get_metadata(self) -> Dict[str, Dict[str, int]]:
        """Return mapping of sprite name to rectangle metadata with page index."""
        return {
            name: {"page": page, "x": r.x, "y": r.y, "width": r.width, "height": r.height}
            for name, (page, r) in self._placements.items()
        }

    def save_atlas(self, path: Union[str, Path]) -> List[Path]:
        """
        Save atlas pages to disk. If multiple pages exist and the filename does not
        contain '{page}', files are suffixed with _0, _1, ...
        Returns the list of saved paths.
        """
        base = Path(path)
        saved: List[Path] = []
        for idx, atlas in enumerate(self._atlases):
            if "{page}" in base.name:
                out_path = base.with_name(base.name.format(page=idx))
            elif len(self._atlases) == 1:
                out_path = base
            else:
                out_path = base.with_name(f"{base.stem}_{idx}{base.suffix}")
            atlas.save(out_path)
            saved.append(out_path)
        return saved

    def save_metadata(self, path: Union[str, Path]) -> Path:
        """
        Save sprite metadata in JSON or YAML format (auto-detected by extension).
        Format: atlas: {width, height, pages}
                pages: [list of atlas filenames]
                sprites: {name: {x, y, width, height, page}}
        Returns the saved path.
        """
        out_path = Path(path)
        
        metadata = {
            "atlas": {
                "width": self.width,
                "height": self.height,
                "pages": len(self._atlases),
            },
            "pages": [f"atlas_{i}.png" for i in range(len(self._atlases))],
            "sprites": {
                name: {"x": r.x, "y": r.y, "width": r.width, "height": r.height, "page": page}
                for name, (page, r) in self._placements.items()
            }
        }
        
        with open(out_path, 'w') as f:
            if out_path.suffix.lower() == '.json':
                json.dump(metadata, f, indent=2)
            else:
                yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
        
        return out_path

    def atlas_images(self) -> List[Image.Image]:
        """Return atlas images (one per page)."""
        return list(self._atlases)

    # Internals --------------------------------------------------------------
    def _ensure_image(self, image: Union[str, Path, Image.Image]) -> Image.Image:
        """Return a PIL image in the configured mode."""
        if isinstance(image, Image.Image):
            return image.convert(self.mode)
        return Image.open(image).convert(self.mode)

    def _ensure_atlas_page(self, page_index: int) -> None:
        """Extend atlas list so the requested page index exists."""
        while len(self._atlases) <= page_index:
            self._atlases.append(self._new_page_image())

    def _new_page_image(self) -> Image.Image:
        """Allocate a blank atlas image."""
        return Image.new(self.mode, (self.width, self.height), self.background)

    def _apply_extrude(self, atlas: Image.Image, image: Image.Image, draw_x: int, draw_y: int) -> None:
        """Repeat edge pixels of the sprite into the padding area."""
        pad = self.padding
        w, h = image.size
        # Edges
        left = image.crop((0, 0, 1, h)).resize((pad, h))
        right = image.crop((w - 1, 0, w, h)).resize((pad, h))
        top = image.crop((0, 0, w, 1)).resize((w, pad))
        bottom = image.crop((0, h - 1, w, h)).resize((w, pad))
        atlas.paste(left, (draw_x - pad, draw_y))
        atlas.paste(right, (draw_x + w, draw_y))
        atlas.paste(top, (draw_x, draw_y - pad))
        atlas.paste(bottom, (draw_x, draw_y + h))

        # Corners
        tl = image.crop((0, 0, 1, 1)).resize((pad, pad))
        tr = image.crop((w - 1, 0, w, 1)).resize((pad, pad))
        bl = image.crop((0, h - 1, 1, h)).resize((pad, pad))
        br = image.crop((w - 1, h - 1, w, h)).resize((pad, pad))
        atlas.paste(tl, (draw_x - pad, draw_y - pad))
        atlas.paste(tr, (draw_x + w, draw_y - pad))
        atlas.paste(bl, (draw_x - pad, draw_y + h))
        atlas.paste(br, (draw_x + w, draw_y + h))
