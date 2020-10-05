#!/usr/bin/env python
"""Preprocessing script from colab notebook

python3 -m process_slices -o $DATA_DIR/expers/geographic/ -p ../conf/geo/postprocess.yaml
"""
from addict import Dict
from glacier_mapping.data.mask import generate_masks
from glacier_mapping.data.slice import write_pair_slices
import argparse
import geopandas as gpd
import glacier_mapping.data.process_slices_funs as pf
import numpy as np
import pandas as pd
import pathlib
import yaml

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Preprocess raw tiffs into slices")
    parser.add_argument("-o", "--output_dir", type=str)
    parser.add_argument("-m", "--slices_meta", type=str)
    parser.add_argument("-p", "--postprocess_conf", type=str, default = "conf/geo/postprocess.yaml")
    args = parser.parse_args()

    # data directories
    output_dir = pathlib.Path(args.output_dir)

    # require that all slices have above filter_percentage[k] for each channel
    pconf = Dict(yaml.safe_load(open(args.postprocess_conf, "r")))
    slice_meta = gpd.read_file(args.slices_meta)
    print("filtering")

    keep_ids = []
    for k, channel in enumerate(pconf.filter_channels):
        cur_ids = pf.filter_directory(
            slice_meta,
            filter_perc=pconf.filter_percentages[k],
            filter_channel=channel
        )
        if len(keep_ids) > 0:
            keep_ids = [x for x in cur_ids if x in keep_ids]
        else:
            keep_ids += cur_ids

    # validation: get ids for the ones that will be training vs. testing.
    print("reshuffling")
    split_fun, split_args = next(iter(pconf.split_method.items()))
    split_fun = getattr(pf, split_fun)
    split_ids = split_fun(keep_ids, slice_meta=slice_meta, **split_args)
    target_locs = pf.reshuffle(split_ids, output_dir)

    # global statistics: get the means and variances in the train split
    print("getting stats")
    pconf.process_funs.normalize.stats_path = \
        pathlib.Path(pconf.process_funs.normalize.stats_path)

    stats = pf.generate_stats(
        [p["img"] for p in target_locs["train"]],
        pconf.normalization_sample_size,
        pconf.process_funs.normalize.stats_path,
    )

    # postprocess individual images (all the splits)
    for split_type in target_locs:
        print(f"postprocessing {split_type}...")
        for i in range(len(target_locs[split_type])):
            img, mask = pf.postprocess(
                target_locs[split_type][i]["img"],
                target_locs[split_type][i]["mask"],
                pconf.process_funs,
            )

            np.save(target_locs[split_type][i]["img"], img)
            np.save(target_locs[split_type][i]["mask"], mask)
