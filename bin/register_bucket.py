#!/usr/bin/env python3

# Import packages
import argparse
import json
import os
import synapseclient

# Parse CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument("--bucket")
parser.add_argument("--base_key")
parser.add_argument("--config")
args = parser.parse_args()

# Log into Synapse with access token or config file
if args.config is not None:
    syn = synapseclient.Synapse(configPath=args.config)
else:
    assert os.environ.get("SYNAPSE_AUTH_TOKEN") is not None
    syn = synapseclient.Synapse()
syn.login(silent=True)

# Get and print storage location ID
destination = {
    "uploadType": "S3",
    "concreteType": "org.sagebionetworks.repo.model.project.ExternalS3StorageLocationSetting",
    "bucket": args.bucket,
    "baseKey": args.base_key,
}
destination = syn.restPOST("/storageLocation", body=json.dumps(destination))
print(destination['storageLocationId'], end="")
