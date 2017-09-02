import argparse

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

import config
import config_context
import cws

# Hard code a config for now.  This should be parsed from a config
# file.
def Config(args):
    return config.Config(
        provider='GCE',
        project=args.project,
        cloud_workstations=[
            config.CwsConfig(
                name='test',
                node=config.NodeConfig(size='n1-standard-2'),
                volumes=[
                    config.VolumeConfig(
                        name='boot',
                        size=50,
                        volume_type='pd-ssd'),
                    config.VolumeConfig(
                        name='data',
                        size=100,
                        volume_type='pd-standard'),
                ],
                location='us-east1-c',
                image_family='debian-9'),
        ])


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


parser = argparse.ArgumentParser(
    description='Tool to manage life cycle of Cloud Workstations')
subparsers = parser.add_subparsers()

# Project should be specified in the config.  Pass this in as a flag
# for now so that I do not leak a specific GCP project id in github.
parser.add_argument('--project', required=True, type=str, help='GCP project ID')

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

if __name__ == '__main__':
    args = parser.parse_args()
    args.func(args)
