#!/usr/bin/env python3

# Import packages
import argparse
import os
import re
import synapseclient


# Parse CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument("--objects")
parser.add_argument("--s3_prefix")
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
s3_prefix = args.s3_prefix.rstrip("/") + "/"
mapping = {s3_prefix: args.parent_id}
with open(args.objects, "r") as infile:
    for line in infile:
        object_uri = line.rstrip()
        head, tail = os.path.split(object_uri)
        head += "/"  # Keep trailing slash for consistency
        relhead = head.replace(s3_prefix, "")
        folder_uri = s3_prefix
        for folder in relhead.rstrip("/").split("/"):
            if folder == "":
                continue
            parent_id = mapping[folder_uri]
            folder_uri += f"{folder}/"
            if folder_uri not in mapping:
                folder_id = create_folder(folder, parent_id)
                mapping[folder_uri] = folder_id
        print(f"{object_uri},{mapping[folder_uri]}")
