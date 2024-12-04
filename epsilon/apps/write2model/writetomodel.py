import epsilon
from scabha.schema_utils import clickify_parameters, paramfile_loader
from scabha.basetypes import File
import os
import glob
from omegaconf import OmegaConf
import click
from epsilon.apps.utilities import CatalogueError
import numpy as np
import dask.array as da
from africanus.dft.dask import im_to_vis
from astropy.coordinates import Angle


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
    
    
    def set_spec(self, freqs):
        self.spectrum = (freqs/self.ref_freq)**self.alpha 

    def calculate_pixel_coordinates(self, l_coord, m_coord, source_l, source_m):
        """
        Method to calculate pixel coordinates of a source in the image plane
        Args:
            l_coord:    l coordinates of image plane
            m_coord:    m coordinates of image plane
            source:     source object
        """
        self.l_pix_coord = np.argmin(np.abs(l_coord - self.l))
        self.m_pix_coord = np.argmin(np.abs(m_coord - self.m))

    
def read_cat(input_skymod, ra0, dec0, freqs, img_size, pix_size):
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
                    Angle(source_params[0]),
                    Angle(source_params[1]),
                    float(source_params[2]),
                    float(source_params[3]),
                    float(source_params[4])
                )
            except:
                raise CatalogueError(f"Error reading source {n+1} in {input_skymod}")
            
            source = Source(ra, dec, flux, alpha, ref_freq)
            source.set_lm(ra0, dec0)
            source.set_spectrum(freqs)
            sources.append(source)
            
            
    # create pixel grid
    npix_l, npix_m = img_size, img_size
    npix_tot = npix_l * npix_m
    refpix_l, refpix_m = npix_l // 2, npix_m // 2
    l_coords = np.sort(np.arange(1 - refpix_l, 1 - refpix_l + npix_l) * pix_size)
    m_coords = np.arange(1 - refpix_m, 1 - refpix_m + npix_m ) * pix_size
    ll, mm = np.meshgrid(l_coords, m_coords)
    # create image hypercube
    intensities = np.zeros((npix_l, npix_m, np.size(freqs), 2))
    for m, source in enumerate(sources):
        source.calculate_pixel_coordinates(ll, mm, source.l, source.m)
        # check if source is within image
        if source.l_pix_coord < 0 or source.l_pix_coord >= npix_l or source.m_pix_coord < 0 or source.m_pix_coord >= npix_m:
            print(f"Warning: Source {m} is outside the image grid")
        intensities[source.l_pix_coord, source.m_pix_coord, :, 0] += source.flux * source.spectrum
    intensities[:, :, :, 1] = intensities[:, :, :, 0] # only Stokes I for now
    lm = np.vstack((ll.flatten(), mm.flatten())).T
    intensities = intensities.reshape(npix_tot,np.size(freqs),2)

    intensities = da.from_array(intensities, chunks=(npix_tot, 1, 1))
    lm = da.from_array(lm, chunks=(npix_tot, 2))
    return intensities, lm





        


@click.command(command)
#@click.version_option(str(epsilon.__version__))
@clickify_parameters(config)
def runit(**kwargs):
    opts = OmegaConf.create(kwargs)
    cat = opts.catalogue
    img_size = opts.image_size
    read_cat(cat)