#!/usr/bin/env python3

# Import packages
import argparse
import os
import re
import synapseclient


# Parse CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument("--objects")
parser.add_argument("--outdir")
parser.add_argument("--parent_id")
parser.add_argument("--config")
args = parser.parse_args()


# Log into Synapse with access token or config file
if args.config is not None:
    syn = synapseclient.Synapse(configPath=args.config)
else:
    assert os.environ.get("SYNAPSE_AUTH_TOKEN") is not None
    syn = synapseclient.Synapse()
syn.login(silent=True)


# Define function for creating folders
def create_folder(name, parent_id):
    entity = {
        "name": name,
        "concreteType": "org.sagebionetworks.repo.model.Folder",
        "parentId": parent_id,
    }
    entity = syn.store(entity)
    return entity.id


# Iterate over S3 "folders"
mapping = {args.outdir: args.parent_id}
with open(args.objects, "r") as infile:
    for line in infile:
        object_uri = line.rstrip()
        head, tail = os.path.split(object_uri)
        relhead = head.replace(args.outdir, "")
        folder_uri = args.outdir
        for folder in relhead.split("/"):
            parent_id = mapping[folder_uri]
            folder_uri += f"{folder}/"
            if folder_uri not in mapping:
                folder_id = create_folder(folder, parent_id)
                mapping[folder_uri] = folder_id
        print(f"{object_uri},{folder_id}")
