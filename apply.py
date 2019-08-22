#!/usr/bin/env python3

import argparse
import os.path
import sys
import subprocess
import yaml


parser = argparse.ArgumentParser(description="Update kubernetes clusters")
parser.add_argument('file', metavar='FILE', type=str, nargs='+')
parser.add_argument('-a', '--all-clusters', help="Apply to all clusters", action='store_true')
parser.add_argument('--dry-run', help="Don't apply changes, just print them", action='store_true')


def get_all_contexts():
    result = subprocess.run(["kubectl", "config", "get-contexts", "-o", "name"], capture_output=True)
    return [context for context in result.stdout.decode('utf-8').split('\n') if context]


def get_current_context():
    result = subprocess.run(["kubectl", "config", "current-context"], capture_output=True)
    return result.stdout.decode('utf-8').strip('\n')


def read_context_config(context):
    fn = "contexts/" + context + ".yaml"
    if not os.path.exists(fn): return {}
    with open(fn, 'r') as f:
        return yaml.load(f, Loader=yaml.Loader)


def apply_config(context, data, dry_run=False):
    args = ["kubectl", "apply", "-f", "-", "--context", context]
    if dry_run:
        args.append("--dry-run")
    result = subprocess.run(args, input=data.encode('utf-8'), stdout=sys.stdout, stderr=sys.stderr)
    if result.returncode != 0:
        raise Exception("Process exited with return code %d" % (result.returncode,))


def main(args):
    if args.all_clusters:
        contexts = get_all_contexts()
    else:
        contexts = [get_current_context()]

    for context in contexts:
        print("Applying to %s..." % (context,))
        config = read_context_config(context)
        for file in args.file:
            print("  applying %s..." % (file,))
            with open(file, 'r') as f:
                data = f.read() % config
                apply_config(context, data, args.dry_run)


if __name__ == '__main__':
    main(parser.parse_args())
