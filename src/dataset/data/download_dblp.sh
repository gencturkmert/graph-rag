#!/bin/bash

# Set variables
DBLP_URL="https://dblp.org/xml/dblp.xml.gz"
DBLP_FILE="dblp.xml.gz"
DBLP_UNZIPPED_FILE="dblp.xml"

# Download the DBLP dataset
echo "Downloading DBLP dataset..."
wget -O $DBLP_FILE $DBLP_URL

# Unzip the dataset
echo "Unzipping the dataset..."
gunzip $DBLP_FILE

echo "Download and extraction complete. The dataset is saved as $DBLP_UNZIPPED_FILE."
