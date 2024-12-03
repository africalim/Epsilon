import epsilon
from scabha.schema_utils import clickify_parameters, paramfile_loader
from scabha.basetypes import File
import os
import glob
from omegaconf import OmegaConf
import click


#BIN = OmegaConf.create({"greet": "greet"

#                        })


command = "greet"
thisdir = os.path.dirname(__file__)

source_files = glob.glob(f"{thisdir}/*.yaml")
sources = [File(item) for item in source_files]
parserfile = File(f"{thisdir}/{command}.yaml")

config = paramfile_loader(parserfile, sources)[command]

@click.command(command)
#@click.version_option(str(epsilon.__version__))
@clickify_parameters(config)
def runit(**kwargs):
    opts = OmegaConf.create(kwargs)
    name = opts.name
    if opts.surname:
        surname = opts.surname
        print(f"Hello {name} {surname}.")
    else:
        print(f"Hello {name}.")

    

