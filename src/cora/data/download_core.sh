#!/bin/bash

# Get the directory of the current script
SCRIPT_DIR=$(dirname "$0")

# URLs of the Cora dataset files
CONTENT_URL="https://linqs-data.soe.ucsc.edu/public/lbc/cora.tgz"

# Download the Cora dataset
echo "Downloading Cora dataset..."
wget $CONTENT_URL -O $SCRIPT_DIR/cora.tgz

# Extract the dataset
echo "Extracting Cora dataset..."
tar -xvzf $SCRIPT_DIR/cora.tgz -C $SCRIPT_DIR

# Clean up
echo "Cleaning up..."
rm $SCRIPT_DIR/cora.tgz

echo "Cora dataset downloaded and extracted to $SCRIPT_DIR"
