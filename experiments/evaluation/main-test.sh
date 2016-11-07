#!/usr/bin/env bash
#
# Execute scripts with test parameters
# Author: Jeanderson Candido
#
./downloader.py "test/download-test.csv" --output "test/verified-subjects.csv"
./main.py "test/verified-subjects.csv" --output "test/raw-data.csv"