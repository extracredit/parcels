from parcels import FieldSet, ParticleSet, ScipyParticle, JITParticle, AdvectionRK4, ParticleFile
from argparse import ArgumentParser
import numpy as np
import pytest
from datetime import timedelta as delta
from os import path

ptype = {'scipy': ScipyParticle, 'jit': JITParticle}


def run_nemo_curvilinear(mode, outfile):
    """Function that shows how to read in curvilinear grids, in this case from NEMO"""
    data_path = path.join(path.dirname(__file__), 'NemoCurvilinear_data/')

    filenames = {'U': data_path + 'U_purely_zonal-ORCA025_grid_U.nc4',
                 'V': data_path + 'V_purely_zonal-ORCA025_grid_V.nc4',
                 'mesh_mask': data_path + 'mesh_mask.nc4'}
    variables = {'U': 'U', 'V': 'V'}
    dimensions = {'U': {'lon': 'nav_lon_u', 'lat': 'nav_lat_u'},
                  'V': {'lon': 'nav_lon_v', 'lat': 'nav_lat_v'}}
    field_set = FieldSet.from_nemo(filenames, variables, dimensions)

    # Now run particles as normal
    npart = 20
    lonp = 30 * np.ones(npart)
    latp = [i for i in np.linspace(-70, 88, npart)]

    def periodicBC(particle, pieldSet, time, dt):
        if particle.lon > 180:
            particle.lon -= 360

    pset = ParticleSet.from_list(field_set, ptype[mode], lon=lonp, lat=latp)
    pfile = ParticleFile(outfile, pset, outputdt=delta(days=1))
    kernels = pset.Kernel(AdvectionRK4) + periodicBC
    pset.execute(kernels, runtime=delta(days=1)*160, dt=delta(hours=6),
                 output_file=pfile)
    assert np.allclose([pset[i].lat - latp[i] for i in range(len(pset))], 0, atol=1e-3)


def make_plot(trajfile):
    from netCDF4 import Dataset
    import matplotlib.pyplot as plt
    from mpl_toolkits.basemap import Basemap

    class ParticleData(object):
        def __init__(self):
            self.id = []

    def load_particles_file(fname, varnames):
        T = ParticleData()
        pfile = Dataset(fname, 'r')
        T.id = pfile.variables['trajectory'][:]
        for v in varnames:
            setattr(T, v, pfile.variables[v][:])
        return T

    T = load_particles_file(trajfile, ['lon', 'lat', 'time'])
    m = Basemap(projection='cyl')
    m.drawparallels(np.arange(-90, 91, 30), labels=[True, False, False, False])
    m.drawmeridians(np.arange(-180, 181, 60), labels=[False, False, False, True])

    T.lon[T.lon > 180] -= 360

    xs, ys = m(T.lon, T.lat)
    m.scatter(xs, ys, c=T.time, s=5)
    plt.show()


@pytest.mark.parametrize('mode', ['jit'])  # Only testing jit as scipy is very slow
def test_nemo_curvilinear(mode):
    outfile = 'nemo_particles'
    run_nemo_curvilinear(mode, outfile)


if __name__ == "__main__":
    p = ArgumentParser(description="""Chose the mode using mode option""")
    p.add_argument('--mode', choices=('scipy', 'jit'), nargs='?', default='jit',
                   help='Execution mode for performing computation')
    args = p.parse_args()

    outfile = "nemo_particles"

    run_nemo_curvilinear(args.mode, outfile)
    make_plot(outfile+'.nc')
