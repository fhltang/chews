# chews: Cheap Workstation

## Objective

Chews is a tool for managing the life cycle of cloud workstations.

By _workstation_, we mean a virtual machine intended to be switched on
and off rather than to be continually running as a server.

See [Design](docs/design.md).

Chews [originally had a more ambitious
objective](docs/original_objective.md) which is currently infeasible.

## Usage

Set up

    virtualenv --no-site-packages --distribute .env && source .env/bin/activate && pip install -r requirements.txt
