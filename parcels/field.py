from scipy.interpolate import RectBivariateSpline
from cached_property import cached_property
from py import path
import numpy as np
from xray import DataArray, Dataset


__all__ = ['Field']


class Field(object):
    """Class that encapsulates access to field data.

    :param name: Name of the field
    :param data: 2D array of field data
    :param lon: Longitude coordinates of the field
    :param lat: Latitude coordinates of the field
    """

    def __init__(self, name, data, lon, lat):
        self.name = name
        self.data = data
        self.lon = lon
        self.lat = lat

    @cached_property
    def interpolator(self):
        return RectBivariateSpline(self.lat, self.lon, self.data)

    def eval(self, x, y):
        return self.interpolator.ev(y, x)

    def write(self, filename, varname=None):
        filepath = str(path.local('%s_%s.nc' % (filename, self.name)))
        if varname is None:
            varname = self.name
        # Derive name of 'depth' variable for NEMO convention
        vname_depth = 'depth%s' % self.name.lower()

        # Create DataArray objects for file I/O
        x, y = (self.lon.size, self.lat.size)
        nav_lon = DataArray(self.lon + np.zeros((y, x)),
                            coords=[('y', self.lat), ('x', self.lon)])
        nav_lat = DataArray(self.lat.reshape(y, 1) + np.zeros(x),
                            coords=[('y', self.lat), ('x', self.lon)])
        vardata = DataArray(np.transpose(self.data).reshape((1, 1, y, x)),
                            coords=[('time_counter', np.zeros(1, dtype=np.float64)),
                                    (vname_depth, np.zeros(1, dtype=np.float)),
                                    ('y', self.lat), ('x', self.lon)])
        # Create xray Dataset and output to netCDF format
        dset = Dataset({varname: vardata}, coords={'nav_lon': nav_lon,
                                                   'nav_lat': nav_lat})
        dset.to_netcdf(filepath)