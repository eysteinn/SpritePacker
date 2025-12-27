#!/usr/bin/env python3
"""Command-line interface for SpritePacker."""

import argparse
import sys
from pathlib import Path

from .packer import SpritePacker


def parse_background(value: str) -> tuple:
    """Parse background color from string format like '0,0,0,0' or '255,255,255'."""
    parts = [int(x.strip()) for x in value.split(',')]
    if len(parts) == 3:
        return tuple(parts) + (255,)  # Add full opacity if not specified
    elif len(parts) == 4:
        return tuple(parts)
    else:
        raise ValueError(f"Background must be 3 or 4 comma-separated integers (got {value})")


def main():
    parser = argparse.ArgumentParser(
        description='Pack sprites into texture atlases using MaxRects algorithm.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Pack a folder of images into a 1024x1024 atlas
  python -m SpritePacker --input sprites/ --output atlas.png --metadata atlas.json

  # Pack with custom settings and extrude mode
  python -m SpritePacker -i sprites/ -o atlas.png -m atlas.yaml --width 2048 --height 2048 --padding 4 --extrude

  # Add specific images
  python -m SpritePacker --image hero.png --image enemy.png -o atlas.png -m atlas.json
        """
    )
    
    # Input options
    input_group = parser.add_argument_group('input options')
    input_group.add_argument(
        '-i', '--input',
        action='append',
        metavar='FOLDER',
        help='Add all images from a folder (can be specified multiple times)'
    )
    input_group.add_argument(
        '--image',
        action='append',
        metavar='FILE',
        help='Add a specific image file (can be specified multiple times)'
    )
    input_group.add_argument(
        '--recursive',
        action='store_true',
        help='Search folders recursively'
    )
    input_group.add_argument(
        '--extensions',
        default='.png,.jpg,.jpeg',
        help='Comma-separated list of file extensions to include (default: .png,.jpg,.jpeg)'
    )
    input_group.add_argument(
        '--no-strip-path',
        action='store_true',
        help='Use full paths as sprite names instead of relative paths'
    )
    
    # Output options
    output_group = parser.add_argument_group('output options')
    output_group.add_argument(
        '-o', '--output',
        required=True,
        help='Output path for atlas image(s) (use {page} for multi-page naming)'
    )
    output_group.add_argument(
        '-m', '--metadata',
        help='Output path for metadata file (.json or .yaml extension)'
    )
    
    # Atlas configuration
    config_group = parser.add_argument_group('atlas configuration')
    config_group.add_argument(
        '--width',
        type=int,
        default=1024,
        help='Atlas page width in pixels (default: 1024)'
    )
    config_group.add_argument(
        '--height',
        type=int,
        default=1024,
        help='Atlas page height in pixels (default: 1024)'
    )
    config_group.add_argument(
        '--padding',
        type=int,
        default=1,
        help='Padding between sprites in pixels (default: 1)'
    )
    config_group.add_argument(
        '--background',
        default='0,0,0,0',
        help='Background color as R,G,B or R,G,B,A (default: 0,0,0,0 = transparent)'
    )
    config_group.add_argument(
        '--mode',
        default='RGBA',
        choices=['RGBA', 'RGB', 'LA', 'L'],
        help='PIL image mode (default: RGBA)'
    )
    config_group.add_argument(
        '--max-pages',
        type=int,
        help='Maximum number of atlas pages (default: unlimited)'
    )
    config_group.add_argument(
        '--extrude',
        action='store_true',
        help='Repeat edge pixels into padding to prevent texture bleeding'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.input and not args.image:
        parser.error('At least one --input folder or --image file must be specified')
    
    # Parse background color
    try:
        background = parse_background(args.background)
    except ValueError as e:
        parser.error(str(e))
    
    # Parse extensions
    extensions = {ext.strip() if ext.startswith('.') else f'.{ext.strip()}'
                  for ext in args.extensions.split(',')}
    
    # Create packer
    try:
        packer = SpritePacker(
            width=args.width,
            height=args.height,
            padding=args.padding,
            background=background,
            mode=args.mode,
            max_pages=args.max_pages,
            extrude=args.extrude
        )
    except ValueError as e:
        print(f"Error creating packer: {e}", file=sys.stderr)
        return 1
    
    # Add images
    try:
        # Add from folders
        if args.input:
            for folder in args.input:
                folder_path = Path(folder)
                if not folder_path.exists():
                    print(f"Warning: Folder not found: {folder}", file=sys.stderr)
                    continue
                if not folder_path.is_dir():
                    print(f"Warning: Not a directory: {folder}", file=sys.stderr)
                    continue
                
                print(f"Adding images from: {folder}")
                packer.add_folder(
                    folder_path,
                    recursive=args.recursive,
                    extensions=extensions,
                    strip_folder_path=not args.no_strip_path
                )
        
        # Add individual images
        if args.image:
            for image_path in args.image:
                img_path = Path(image_path)
                if not img_path.exists():
                    print(f"Warning: Image not found: {image_path}", file=sys.stderr)
                    continue
                if not img_path.is_file():
                    print(f"Warning: Not a file: {image_path}", file=sys.stderr)
                    continue
                
                print(f"Adding image: {image_path}")
                name = img_path.name
                packer.add_image(name, img_path)
        
    except ValueError as e:
        print(f"Error adding images: {e}", file=sys.stderr)
        return 1
    
    # Save atlas
    try:
        print(f"\nSaving atlas to: {args.output}")
        saved_paths = packer.save_atlas(args.output)
        for path in saved_paths:
            print(f"  Created: {path}")
    except Exception as e:
        print(f"Error saving atlas: {e}", file=sys.stderr)
        return 1
    
    # Save metadata if requested
    if args.metadata:
        try:
            print(f"\nSaving metadata to: {args.metadata}")
            metadata_path = packer.save_metadata(args.metadata)
            print(f"  Created: {metadata_path}")
        except Exception as e:
            print(f"Error saving metadata: {e}", file=sys.stderr)
            return 1
    
    # Print summary
    metadata = packer.get_metadata()
    print(f"\n✓ Successfully packed {len(metadata)} sprite(s) into {len(saved_paths)} page(s)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
