import click
#from scabha.schema_utils import clickify_parameters, paramfile_loader


@click.command()
@click.argument('name')

def greet(name):
    click.echo(f"hello {name}")

