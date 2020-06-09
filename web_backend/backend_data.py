#!/usr/bin/env python
"""
Utilities for Managing VRTs

2020-05-05 18:11:08
"""
from osgeo import gdal
import argparse
import fiona
import numpy as np
import pandas as pd
import pathlib
import glob
import rasterio
import shapely.geometry
import subprocess


def reproject_directory(input_dir, output_dir, dst_epsg=4326):
    inputs = pathlib.Path(input_dir).glob("*.tif")
    for im_path in inputs:
        print(f"reprojecting {str(im_path)}")
        im = rasterio.open(im_path)
        output_path = pathlib.Path(output_dir, f"{im_path.stem}-warped.tif")
        subprocess.call(["gdalwarp", "-s_srs", str(im.crs), "-t_srs",
                         f"EPSG:{dst_epsg}", str(im_path),
                         "-wo", "NUM_THREADS=ALL_CPUS", str(output_path)])


def vrt_from_dir(input_dir, output_path="./output.vrt", **kwargs):
    inputs = glob.glob(f"{input_dir}*.tif")
    vrt_opts = gdal.BuildVRTOptions(**kwargs)
    gdal.BuildVRT(output_path, inputs, options=vrt_opts)


def tiles(input_vrt, output_dir, zoom_levels="10"):
    path = pathlib.Path(input_vrt)
    intermediate = f"{path.parent}/{path.resolve().stem}-byte.vrt"
    subprocess.call(["gdal_translate", "-ot", "Byte", input_vrt, f'{intermediate}'])
    gdal2tiles.generate_tiles(f"{intermediate}", output_dir, zoom=zoom_levels, verbose=True, tile_size=1056)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge to a VRT")
    parser.add_argument("-d", "--input_dir", type=str)
    parser.add_argument("-o", "--output_dir", type=str, default="./")
    parser.add_argument("-n", "--output_name", type=str, default="output.vrt")
    parser.add_argument("-t", "--tile", default=False)
    args = parser.parse_args()

    reproject_directory(args.input_dir, args.output_dir)
    vrt_path = pathlib.Path(args.output_dir, args.output_name)
    vrt_from_dir(args.output_dir, str(vrt_path))
    if args.tile:
        tiles(vrt_path, args.output_dir)
