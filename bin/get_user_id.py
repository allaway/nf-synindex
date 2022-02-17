#!/usr/bin/env python3

# Import packages
import argparse
import os
import synapseclient

# Parse CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument("--config")
args = parser.parse_args()

# Log into Synapse with access token or config file
if args.config is not None:
    syn = synapseclient.Synapse(configPath=args.config)
else:
    assert os.environ.get("SYNAPSE_AUTH_TOKEN") is not None
    syn = synapseclient.Synapse()
syn.login(silent=True)

# Get and print user ID
user = syn.getUserProfile()
print(user.ownerId, end="")
