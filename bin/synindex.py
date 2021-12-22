#!/usr/bin/env python3

# Import packages
import argparse
import hashlib
import json
import os
import re
import synapseclient

# Parse CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument("--storage_id")
parser.add_argument("--file")
parser.add_argument("--uri")
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


# Compute MD5 checksum
# Credit: https://stackoverflow.com/a/3431838
hash_md5 = hashlib.md5()
with open(args.file, "rb") as f:
    for chunk in iter(lambda: f.read(4096), b""):
        hash_md5.update(chunk)
checksum = hash_md5.hexdigest()


# Create a file handle for an S3 object
filename = os.path.basename(args.file)
bucket, key = re.fullmatch(r"s3://([^/]+)/(.*)", args.s3_uri).groups()
fileHandle = {
    "concreteType": "org.sagebionetworks.repo.model.file.S3FileHandle",
    "storageLocationId": args.storage_id,
    "fileName": filename,
    "contentMd5": checksum,
    "bucketName": bucket,
    "key": key,
}
fileHandle = syn.restPOST(
    "/externalFileHandle/s3", json.dumps(fileHandle), endpoint=syn.fileHandleEndpoint
)


# Expose that file handle on Synapse with a File
file = synapseclient.File(
    name=fileHandle["fileName"],
    parentId=args.parent_id,
    dataFileHandleId=fileHandle["id"],
)
file = syn.store(file)
print(f"{args.s3_uri},{file.id}")
