import epsilon
from scabha.schema_utils import clickify_parameters, paramfile_loader
from scabha.basetypes import File
import os
import glob
from omegaconf import OmegaConf
import click
from epsilon.apps.utilities import CatalogueError
import numpy as np


#BIN = OmegaConf.create({"greet": "greet"

#                        })


command = "predict"
thisdir = os.path.dirname(__file__)

source_files = glob.glob(f"{thisdir}/*.yaml")
sources = [File(item) for item in source_files]
parserfile = File(f"{thisdir}/{command}.yaml")

config = paramfile_loader(parserfile, sources)[command]

class Source:
    def __init__(self, ra, dec, flux, alpha, ref_freq):
 
        self.ra = ra
        self.dec = dec
        self.flux = flux
        self.alpha = alpha
        self.ref_freq = ref_freq
        self.spectrum = None

    def radec2lm(self, ra0, dec0):
        dra = self.ra - ra0
        self.l = np.cos(self.dec) * np.sin(dra) 
        self.m = np.sin(self.dec) * np.cos(dec0) - np.cos(self.dec) * np.sin(dec0) * np.cos(dra)
    
        return self.l, self.m
    
    def set_spec(self, freqs):
        self.spectrum = (freqs/self.ref_freq)**self.alpha 

    
def read_cat(input_skymod):
    sources = []
    with open(input_skymod) as input_sources:

        header = input_sources.readline().strip()

        header = header.strip().replace("#", "").strip()
        header = header.split(' ')

        for n, line in enumerate(input_sources.readlines()):
            # skip header line
            if line.startswith("#"):
                continue
            # get source info
            source_params = line.strip().split(' ')
            if len(source_params) != len(header):
                raise CatalogueError("The number of elements in one or more rows does not equal the\
                                    number of expected elements based on the number of elements in the\
                                    header")
            try:
                ra, dec, flux, alpha, ref_freq = (
                    source_params[0],
                    source_params[1],
                    float(source_params[2]),
                    float(source_params[3]),
                    float(source_params[4])
                )
            except:
                raise CatalogueError(f"Error reading source {n+1} in {input_skymod}")
            
            sources.append(Source(ra, dec, flux, alpha, ref_freq))
            
    print(f'ra: {sources[0].ra}, dec: {sources[0].dec}, flux: {sources[0].flux}, alpha: {sources[0].alpha}, reference frequency: {sources[0].ref_freq}')
                
            


@click.command(command)
#@click.version_option(str(epsilon.__version__))
@clickify_parameters(config)
def runit(**kwargs):
    opts = OmegaConf.create(kwargs)
    cat = opts.catalogue
    read_cat(cat)