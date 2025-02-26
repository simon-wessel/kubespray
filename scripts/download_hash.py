#!/usr/bin/env python3

# After a new version of Kubernetes has been released,
# run this script to update roles/download/defaults/main/main.yml
# with new hashes.

import sys

import requests
from ruamel.yaml import YAML

MAIN_YML = "../roles/download/defaults/main/main.yml"

def open_main_yaml():
    yaml = YAML()
    yaml.explicit_start = True
    yaml.preserve_quotes = True
    yaml.width = 4096

    with open(MAIN_YML, "r") as main_yml:
        data = yaml.load(main_yml)

    return data, yaml


def download_hash(versions):
    architectures = ["arm", "arm64", "amd64", "ppc64le"]
    downloads = ["kubelet", "kubectl", "kubeadm"]

    data, yaml = open_main_yaml()

    for download in downloads:
        checksum_name = f"{download}_checksums"
        for arch in architectures:
            for version in versions:
                if not version.startswith("v"):
                    version = f"v{version}"
                url = f"https://dl.k8s.io/release/{version}/bin/linux/{arch}/{download}.sha256"
                hash_file = requests.get(url, allow_redirects=True)
                if hash_file.status_code == 404:
                    raise Exception(f"Unable to find hash file for release {version} (arch: {arch})")
                if hash_file.status_code != 200:
                    raise Exception(f"Received a non-200 HTTP response code: {hash_file.status_code} (arch: {arch}, version: {version})")
                sha256sum = hash_file.content.decode().strip()
                if len(sha256sum) != 64:
                    raise Exception(f"Checksum has an unexpected length: {len(sha256sum)} (arch: {arch}, version: {version})")
                if checksum_name not in data:
                    data[checksum_name] = {}
                if arch not in data[checksum_name]:
                    data[checksum_name][arch] = {}
                data[checksum_name][arch][version] = sha256sum

    with open(MAIN_YML, "w") as main_yml:
        yaml.dump(data, main_yml)
        print(f"\n\nUpdated {MAIN_YML}\n")


def usage():
    print(f"USAGE:\n    {sys.argv[0]} [k8s_version1] [[k8s_version2]....[k8s_versionN]]")


def main(argv=None):
    if not argv:
        argv = sys.argv[1:]
    if not argv:
        usage()
        return 1
    download_hash(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
