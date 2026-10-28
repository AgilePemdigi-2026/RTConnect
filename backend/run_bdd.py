#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RTConnect BDD Test Runner for Gherkin Scenarios (.gherkin)
Enables native execution of .gherkin specification files aligned with GitHub issues.
"""

import sys
import os

# Ensure backend root is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import behave.runner_util as ru
from behave.runner_util import FileLocation, FileLocationParser, FeatureListParser, InvalidFilenameError
from behave.runner import Runner
from behave.__main__ import main as behave_main

# Patch behave to accept .gherkin extension alongside .feature
original_collect = ru.collect_feature_locations

def patched_collect_feature_locations(paths, strict=True):
    locations = []
    for path in paths:
        if os.path.isdir(path):
            for dirpath, dirnames, filenames in os.walk(path, followlinks=True):
                dirnames.sort()
                for filename in sorted(filenames):
                    if filename.endswith(".feature") or filename.endswith(".gherkin"):
                        location = FileLocation(os.path.join(dirpath, filename))
                        locations.append(location)
        elif path.startswith('@'):
            locations.extend(FeatureListParser.parse_file(path[1:]))
        else:
            location = FileLocationParser.parse(path)
            if not (location.filename.endswith(".feature") or location.filename.endswith(".gherkin")):
                raise InvalidFilenameError(location.filename)
            if location.exists():
                locations.append(location)
            elif strict:
                raise FileNotFoundError(path)
    return locations

ru.collect_feature_locations = patched_collect_feature_locations
import behave.runner as behave_runner
behave_runner.collect_feature_locations = patched_collect_feature_locations

# 2. Patch Runner.setup_paths to recognize .gherkin files during path discovery
original_setup_paths = Runner.setup_paths

def patched_setup_paths(self):
    orig_walk = os.walk
    def walk_with_gherkin(top, **kwargs):
        for root, dirs, files in orig_walk(top, **kwargs):
            mapped_files = [f if not f.endswith('.gherkin') else f + '.feature' for f in files]
            yield root, dirs, mapped_files
    
    os.walk = walk_with_gherkin
    try:
        return original_setup_paths(self)
    finally:
        os.walk = orig_walk

Runner.setup_paths = patched_setup_paths

def run():
    features_dir = os.path.join(backend_dir, 'features')
    args = sys.argv[1:]
    
    # If no paths specified, default to features directory
    has_path = any(not a.startswith('-') for a in args)
    if not has_path:
        args = [features_dir] + args

    print("=" * 60)
    print("      MEMULAI PENGUJIAN BDD RTCONNECT (.gherkin)      ")
    print(f"  Target Direktori : {features_dir}")
    print(f"  Argumen Eksekusi : {' '.join(args)}")
    print("=" * 60)

    exit_code = behave_main(args)
    sys.exit(exit_code)

if __name__ == '__main__':
    run()
