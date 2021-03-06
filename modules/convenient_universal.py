"""Collection of convenient functions that will work with my anaconda or uvcdat install.

Functions:
  adjust_lon_range   -- Express longitude values in desired 360 degree interval
  apply_lon_filter   -- Set values outside of specified longitude range to zero
  broadcast_array    -- Broadcast an array to a target shape
  calc_significance  -- Perform significance test
  coordinate_paris   -- Generate lat/lon pairs
  dict_filter        -- Filter dictionary according to specified keys
  find_nearest       -- Find the closest array item to value
  find_duplicates    -- Return list of duplicates in a list
  fix_label          -- Fix formatting of an axis label taken from the command line
  get_threshold      -- Turn the user input threshold into a numeric threshold
  hi_lo              -- Determine the new highest and lowest value.
  list_kwargs        -- List keyword arguments of a function
  match_dates        -- Take list of dates and match with the corresponding times 
                        in a detailed time axis
  single2list        -- Check if item is a list, then convert if not
  units_info         -- Make the units taken from a file LaTeX math compliant

"""

import numpy
from scipy import stats
import pdb, re
import inspect


def adjust_lon_range(lons, radians=True, start=0.0):
    """Express longitude values in a 360 degree (or 2*pi radians) interval.

    Args:
      lons (list/tuple): Longitude axis values (monotonically increasing)
      radians (bool): Specify whether input data are in radians (True) or
        degrees (False). Output will be the same units.
      start (float, optional): Start value for the output interval (add 360 degrees or 2*pi
        radians to get the end point)
    
    """
    
    lons = single2list(lons, numpy_array=True)    
    
    interval360 = 2.0*numpy.pi if radians else 360.0
    end = start + interval360    
    
    less_than_start = numpy.ones([len(lons),])
    while numpy.sum(less_than_start) != 0:
        lons = numpy.where(lons < start, lons + interval360, lons)
        less_than_start = lons < start
    
    more_than_end = numpy.ones([len(lons),])
    while numpy.sum(more_than_end) != 0:
        lons = numpy.where(lons >= end, lons - interval360, lons)
        more_than_end = lons >= end

    return lons


def apply_lon_filter(data, lon_bounds):
    """Set values outside of specified longitude range to zero.

    Args:
      data (numpy.ndarray): Array of longitude values.
      lon_bounds (list/tuple): Specified longitude range (min, max)

    """
    
    # Convert to common bounds (0, 360)
    lon_min = adjust_lon_range(lon_bounds[0], radians=False, start=0.0)
    lon_max = adjust_lon_range(lon_bounds[1], radians=False, start=0.0)
    lon_axis = adjust_lon_range(data.getLongitude()[:], radians=False, start=0.0)

    # Make required values zero
    ntimes, nlats, nlons = data.shape
    lon_axis_tiled = numpy.tile(lon_axis, (ntimes, nlats, 1))
    
    new_data = numpy.where(lon_axis_tiled < lon_min, 0.0, data)
    
    return numpy.where(lon_axis_tiled > lon_max, 0.0, new_data)


def broadcast_array(array, axis_index, shape):
    """Broadcast an array to a target shape.
    
    Args:
      array (numpy.ndarray)
      axis_index (int or tuple): Postion in the target shape that the 
        axis/axes of the array corresponds to
          e.g. if array corresponds to (depth, lat, lon) in (time, depth, lat, lon)
          then axis_index = [1, 3]
          e.g. if array corresponds to (lat) in (time, depth, lat, lon)
          then axis_index = 2
      shape (tuple): shape to broadcast to
      
    For a one dimensional array, make start_axis_index = end_axis_index
    
    """

    if type(axis_index) in [float, int]:
        start_axis_index = end_axis_index = axis_index
    else:
        assert len(axis_index) == 2
        start_axis_index, end_axis_index = axis_index
    
    dim = start_axis_index - 1
    while dim >= 0:
        array = array[numpy.newaxis, ...]
        array = numpy.repeat(array, shape[dim], axis=0)
        dim = dim - 1
    
    dim = end_axis_index + 1
    while dim < len(shape):    
        array = array[..., numpy.newaxis]
        array = numpy.repeat(array, shape[dim], axis=-1)
        dim = dim + 1

    return array


def calc_significance(data_subset, data_all, standard_name):
    """Perform significance test.

    One sample t-test, with sample size adjusted for autocorrelation.
    
    Reference:
      Zieba (2010). doi:10.2478/v10178-010-0001-0
    
    """

    from statsmodels.tsa.stattools import acf

    # Data must be three dimensional, with time first
    assert len(data_subset.shape) == 3, "Input data must be 3 dimensional"
    
    # Define autocorrelation function
    n = data_subset.shape[0]
    autocorr_func = numpy.apply_along_axis(acf, 0, data_subset, nlags=n - 2)
    
    # Calculate effective sample size (formula from Zieba2010, eq 12)
    k = numpy.arange(1, n - 1)
    
    r_k_sum = ((n - k[:, None, None]) / float(n)) * autocorr_func[1:] 
    n_eff = float(n) / (1 + 2 * r_k_sum.sum(axis=0))
    
    # Calculate significance
    var_x = data_subset.var(axis=0) / n_eff
    tvals = (data_subset.mean(axis=0) - data_all.mean(axis=0)) / numpy.sqrt(var_x)
    pvals = stats.t.sf(numpy.abs(tvals), n - 1) * 2  # two-sided pvalue = Prob(abs(t)>tt)

    notes = "One sample t-test, with sample size adjusted for autocorrelation (Zieba2010, eq 12)" 
    pval_atts = {'standard_name': standard_name,
                 'long_name': standard_name,
                 'units': ' ',
                 'notes': notes,}

    return pvals, pval_atts


def coordinate_pairs(lat_axis, lon_axis):
    """Take the latitude and longitude values from given grid axes
    and produce a flattened lat and lon array, with element-wise pairs 
    corresponding to every grid point."""
    
    lon_mesh, lat_mesh = numpy.meshgrid(lon_axis, lat_axis)  # This is the correct order
    
    return lat_mesh.flatten(), lon_mesh.flatten()


def dict_filter(indict, key_list):
    """Filter dictionary according to specified keys."""
    
    return dict((key, value) for key, value in indict.iteritems() if key in key_list)


def find_duplicates(inlist):
    """Return list of duplicates in a list."""
    
    D = defaultdict(list)
    for i,item in enumerate(mylist):
        D[item].append(i)
    D = {k:v for k,v in D.items() if len(v)>1}
    
    return D


def find_nearest(array, value):
    """Find the closest array item to value."""
    
    idx = (numpy.abs(numpy.array(array) - value)).argmin()
    return array[idx]


def fix_label(label):
    """Fix axis label taken from the command line."""

    replace_dict = {'_': ' ',
                    'degE': '$^{\circ}$E',
                    'ms-1': '$m s^{-1}$',
                    'm.s-1': '$m s^{-1}$',
                    '1000000 m2.s-1': '$10^6$m$^2$s$^{-1}$'
                   } 

    for value, replacement in replace_dict.iteritems():
        label = label.replace(value, replacement)

    return label 


def get_threshold(data, threshold_str, axis=None):
    """Turn the user input threshold into a numeric threshold."""
    
    if 'pct' in threshold_str:
        value = float(re.sub('pct', '', threshold_str))
        threshold_float = numpy.percentile(data, value, axis=axis)
    else:
        threshold_float = float(threshold_str)
    
    return threshold_float


def hi_lo(data_series, current_max, current_min):
    """Determine the new highest and lowest value."""
    
    try:
        highest = numpy.max(data_series)
    except:
        highest = max(data_series)
    
    if highest > current_max:
        new_max = highest
    else:
        new_max = current_max
    
    try:    
        lowest = numpy.min(data_series)
    except:
        lowest = min(data_series)
    
    if lowest < current_min:
        new_min = lowest
    else:
        new_min = current_min
    
    return new_max, new_min


def list_kwargs(func):
    """List keyword arguments of a function."""
    
    details = inspect.getargspec(func)
    nopt = len(details.defaults)
    
    return details.args[-nopt:]


def match_dates(datetimes, datetime_axis):
    """Take list of datetimes and match with the corresponding datetimes in a time axis.
 
    Args:   
      datetimes (list/tuple)
      datetime_axis (list/tuple)
        
    """

    dates = map(split_dt, datetimes)
    date_axis = map(split_dt, datetime_axis[:]) 
    
    match_datetimes = []
    miss_datetimes = [] 

    for i in range(0, len(datetime_axis)):
        if date_axis[i] in dates:
            match_datetimes.append(datetime_axis[i])
        else:
            miss_datetimes.append(datetime_axis[i])    

    return match_datetimes, miss_datetimes


def split_dt(dt):
    """Split a numpy.datetime64 value so as to just keep the date part."""

    return str(dt).split('T')[0]


def single2list(item, numpy_array=False):
    """Check if item is a list, then convert if not."""
    
    if type(item) == list or type(item) == tuple or type(item) == numpy.ndarray:
        output = item 
    elif type(item) == str:
        output = [item,]
    else:
        try:
            test = len(item)
        except TypeError:
            output = [item,]

    if numpy_array and not isinstance(output, numpy.ndarray):
        return numpy.array(output)
    else:
        return output


def units_info(units):
    """Make the units taken from a file LaTeX math compliant.
    
    This function particularly deals with powers:
      e.g. 10^22 J
    """

    index = units.find('^')
    units = units[:index + 1] + '{' + units[index + 1:]

    index = units.find('J')
    units = units[:index - 1] + '}' + units[index - 1:]

    tex_units = '$'+units+'$'
    exponent = tex_units.split('}')[0].split('{')[1]

    return tex_units, exponent

