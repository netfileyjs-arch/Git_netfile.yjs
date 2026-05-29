#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib
import json

config_path = 'system_config.json'

with open(config_path, 'rb') as f:
    content = f.read()
    hash_value = hashlib.sha256(content).hexdigest()

print(f"SHA256: {hash_value}")

# Write hash to file
hash_file = config_path.replace('.json', '.sha256')
with open(hash_file, 'w') as f:
    f.write(hash_value + '\n')

print(f"Hash saved to: {hash_file}")
