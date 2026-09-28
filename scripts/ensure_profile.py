#!/usr/bin/env python3
"""Add a CLI profile that assumes OrganizationAccountAccessRole in a member account - only if it is missing.

Usage:  python3 scripts/ensure_profile.py <profile-name> <account-id>
It backs up ~/.aws/config first, never edits or removes an existing section, and leaves [default] alone.
"""
import configparser, os, shutil, sys

name, account = sys.argv[1], sys.argv[2]
path = os.path.expanduser("~/.aws/config")
section = f"profile {name}"
cfg = configparser.RawConfigParser()
cfg.read(path)
if cfg.has_section(section):
    print(f"{name}: already present - left unchanged ({cfg.get(section, 'role_arn', fallback='no role_arn')})")
    sys.exit(0)
shutil.copy(path, path + ".bak")
with open(path, "a") as f:
    f.write(f"\n[{section}]\nrole_arn = arn:aws:iam::{account}:role/OrganizationAccountAccessRole\n"
            f"source_profile = default\nregion = us-east-1\n")
print(f"{name}: added (backup at {path}.bak)")
