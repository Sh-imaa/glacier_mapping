#!/usr/bin/env python
"""
Training/Eval Pipeline:
    1- Initialize loaders (train & validation)
        1.1-Pass all params onto both loaders
    2- Initialize the framework
    3- Train Loop 10 epochs
        3.1 Pass entire data loader through epoch
        3.2 Iterate over dataloader with specific batch
    4- Log Epoch level train acc, test acc, train loss, test loss.
    5- Save checkpoints after 5 epochs

"""
from pathlib import Path
from src.data import GlacierDataset
from src.frame import Framework
from torch.utils.data import DataLoader, Subset
import yaml
import addict
from torch.utils.tensorboard import SummaryWriter
import torch
from pathlib import Path
import argparse

## Train Loop
def train(train_loader, val_loader, frame, writer, epochs=20):
   
    for epoch in range(1, epochs):
        loss = 0
        metrics = {k : 0 for k in frame.metrics_opts.keys()}
        for i, (x,y) in enumerate(train_loader):
            frame.set_input(x,y)
            loss += frame.optimize()

            # metrics added to values of current iteration
            current_metrics = frame.calculate_metrics()
            metrics = update_metrics(metrics, current_metrics)

        print("Epoch metrics:", metrics)
        print("epoch Loss:", loss / len(train_dataset))
        writer.add_scalar('Epoch Loss', loss/len(train_dataset), epoch)
        for k,v in metrics.items():
            writer.add_scalar('Train Epoch Metrics ' + k, v/len(train_dataset), epoch)
        if epoch%5==0:
            frame.save(frame.out_dir, epoch)

        ## validation loop
        loss = 0
        metrics = {k : 0 for k in frame.metric_opts.keys()}
        for i, (x,y) in enumerate(val_loader):
            frame.set_input(x,y)
            y_hat = frame.infer(frame.x)
            loss += frame.loss(y_hat,frame.y).item()
        
            current_metrics = frame.calculate_metrics()
            metrics = update_metrics(metrics, current_metrics)

        writer.add_scalar('Batch Val Loss', loss/len(val_dataset), epoch)
        print("val Loss: ", loss / len(val_loader))
        
        for k,v in metrics.items():
            writer.add_scalar('Val Epoch Metrics ' + k, v/len(val_dataset), epoch)

        
def update_metrics(d1, d2):
    d3 = {}
    for k in d1.keys():
        d3[k] = d1[k]+d2[k]
    return d3



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--conf",
        type=str,
        default="shared/train.yaml",
        help="path to the yaml file specifying training options"
    )
    parser.add_argument(
        "-p",
        "--path",
        type=str,
        default="/scratch/akera/glaciers/processed/",
        help="path to the data on which to train"
    )
    parser.add_argument(
        "-s",
        "--subset",
        type=int,
        default=-1,
        help="Optionally subset to first S datapoints during training / validation"
    )
    parser.add_argument(
        "-w",
        "--num_workers",
        type=int,
        default=10,
        help="Number of workers to use during loading"
    )

    args = parser.parse_args()

    train_dataset = GlacierDataset(Path(args.path, "train"))
    val_dataset = GlacierDataset(Path(args.path, "test"))

    if args.subset != -1:
        train_dataset = Subset(train_dataset, range(args.subset))
        val_dataset = Subset(val_dataset, range(args.subset))

    # import pdb
    # pdb.set_trace()
    train_opts = addict.Dict(yaml.load(open(args.conf)))

    train_loader = DataLoader(train_dataset,batch_size=train_opts.loop.train_batch_size, shuffle=True, num_workers=args.num_workers)
    val_loader = DataLoader(val_dataset, batch_size=train_opts.loop.val_batch_size, shuffle=True, num_workers=args.num_workers)

    
    frame = Framework(model_opts=train_opts.model, optimizer_opts=train_opts.optim, metrics_opts=train_opts.metrics)
    writer = SummaryWriter()
    train(train_loader, val_loader, frame, writer, epochs=train_opts.loop.epochs)
