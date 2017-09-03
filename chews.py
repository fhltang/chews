#!.env/bin/python 

import argparse

from google.protobuf import text_format
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

from genfiles import config_pb2
import config_context
import cws

# Hard code a config for now.  This should be parsed from a config
# file.
def Config(args):
    config = config_pb2.Config()
    with open(args.config_file) as f:
        text_format.Merge(f.read(), config)

    # Optionally override config fields.
    if args.project:
        config.project = args.project

    config_context.ConfigValidator(config).validate()

    return config


def create(args):
    ctx = config_context.ConfigContext(Config(args))
    workstation = cws.Cws(ctx, args.name)
    workstation.create()


def stop(args):
    ctx = config_context.ConfigContext(Config(args))
    workstation = cws.Cws(ctx, args.name)
    workstation.stop()


def dessicate(args):
    ctx = config_context.ConfigContext(Config(args))
    workstation = cws.Cws(ctx, args.name)
    workstation.dessicate()


def rehydrate(args):
    ctx = config_context.ConfigContext(Config(args))
    workstation = cws.Cws(ctx, args.name)
    workstation.rehydrate()


def powerup(args):
    ctx = config_context.ConfigContext(Config(args))
    workstation = cws.Cws(ctx, args.name)
    workstation.powerup()


def powerdown(args):
    ctx = config_context.ConfigContext(Config(args))
    workstation = cws.Cws(ctx, args.name)
    workstation.powerdown()


def tidysnapshots(args):
    ctx = config_context.ConfigContext(Config(args))
    workstation = cws.Cws(ctx, args.name)
    workstation.tidy_snapshots()


def printstatus(args):
    ctx = config_context.ConfigContext(Config(args))
    workstation = cws.Cws(ctx, args.name)
    print(workstation.state())


def printconfig(args):
    config = Config(args)
    print text_format.MessageToString(config)


parser = argparse.ArgumentParser(
    description='Tool to manage life cycle of Cloud Workstations')
subparsers = parser.add_subparsers()

# Project should be specified in the config.  Pass this in as a flag
# for now so that I do not leak a specific GCP project id in github.
parser.add_argument('--project', type=str, help='GCP project ID')
parser.add_argument('--config_file', type=str, help='Path to configuration file', required=True)

create_parser = subparsers.add_parser('create')
create_parser.add_argument('name')
create_parser.set_defaults(func=create)

stop_parser = subparsers.add_parser('stop')
stop_parser.add_argument('name')
stop_parser.set_defaults(func=stop)

dessicate_parser = subparsers.add_parser('dessicate')
dessicate_parser.add_argument('name')
dessicate_parser.set_defaults(func=dessicate)

rehydrate_parser = subparsers.add_parser('rehydrate')
rehydrate_parser.add_argument('name')
rehydrate_parser.set_defaults(func=rehydrate)

powerup_parser = subparsers.add_parser('powerup')
powerup_parser.add_argument('name')
powerup_parser.set_defaults(func=powerup)

powerdown_parser = subparsers.add_parser('powerdown')
powerdown_parser.add_argument('name')
powerdown_parser.set_defaults(func=powerdown)

tidysnapshots_parser = subparsers.add_parser('tidysnapshots')
tidysnapshots_parser.add_argument('name')
tidysnapshots_parser.set_defaults(func=tidysnapshots)

printstatus_parser = subparsers.add_parser('printstatus')
printstatus_parser.add_argument('name')
printstatus_parser.set_defaults(func=printstatus)

printconfig_parser = subparsers.add_parser('printconfig')
printconfig_parser.set_defaults(func=printconfig)

if __name__ == '__main__':
    args = parser.parse_args()
    args.func(args)
