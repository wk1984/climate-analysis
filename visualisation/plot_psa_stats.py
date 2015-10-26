# Import general Python modules

import os, sys, pdb, itertools
import math
import numpy
import pandas
import argparse
from scipy import stats
from scipy.signal import argrelextrema
import pyqt_fit

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import matplotlib.font_manager as font_manager

import seaborn
seaborn.set_context("paper")
seaborn.set_palette("deep") #"colorblind"
palette = itertools.cycle(seaborn.color_palette())

# Import my modules

cwd = os.getcwd()
repo_dir = '/'
for directory in cwd.split('/')[1:]:
    repo_dir = os.path.join(repo_dir, directory)
    if directory == 'climate-analysis':
        break

modules_dir = os.path.join(repo_dir, 'modules')
sys.path.append(modules_dir)

try:
    import general_io as gio
    import convenient_universal as uconv
except ImportError:
    raise ImportError('Must run this script from anywhere within the climate-analysis git repo')


# Define functions

season_months = {'annual': None, 'DJF': (12, 1, 2), 'MAM': (3, 4, 5), 
                 'JJA': (6, 7, 8), 'SON': (9, 10, 11)}

def kde_stats(kde_data, kde_bins, width, label):
    """Print kde stats to the screen."""
    
    local_maxima = argrelextrema(kde_data, numpy.greater)
    local_minima = argrelextrema(kde_data, numpy.less)
    
    print label
    print "Local maxima"
    for maxima_index in local_maxima[0]:
        print broad_extrema(width, maxima_index, kde_data, kde_bins, 'maxima')

#    print "Local minima"
#    for minima_index in local_minima[0]:
#        print broad_extrema(width, minima_index, kde_data, kde_bins, 'minima')


def broad_extrema(width, extrema_index, data, bins, extrema_type):
    """Select the n largest/smallest values around an extrema."""
    
    assert extrema_type in ['maxima', 'minima']
    
    left_index = extrema_index
    right_index = extrema_index
    for i in range(0, width):
        right_value = data[right_index + 1]
        left_value = data[left_index - 1]
        
        if extrema_type == 'maxima':
            if right_value >= left_value:
                right_index = right_index + 1
            else:
                left_index = left_index - 1
        elif extrema_type == 'minima':
            if right_value <= left_value:
                right_index = right_index + 1
            else:
                left_index = left_index - 1
    
    return bins[left_index], bins[right_index]


def gradient_stats(gradient_list):
    """Print gradient statistics to screen"""
    
    print "gradient mean:", numpy.mean(gradient_list)
    print "gradient std:", numpy.std(gradient_list)


def plot_phase_progression(ax, df, freq, gradient_limit):
    """Create the plot showing how the phase changes over time."""
    
    amp_max = df['env_max'].max()
    amp_min = df['env_max'].min()
    duration_max =  df['event_duration'].max()
    event_numbers = numpy.unique(df['event_number'].values)
    
    all_gradients = []
    for event in event_numbers:
        phase_data = df['event_phase'].loc[df['event_number'] == event].values
        amp_data = df['env_max'].loc[df['event_number'] == event].values
        gradient = df['event_gradient'].loc[df['event_number'] == event].values[0]
        x_axis = numpy.arange(0, len(phase_data))

        all_gradients.append(gradient)
        if gradient > gradient_limit:
            cmap = seaborn.light_palette('red', as_cmap=True)
        elif gradient < -(gradient_limit):
            cmap = seaborn.light_palette('blue', as_cmap=True)
        else:
            cmap = seaborn.light_palette('grey', as_cmap=True)

        points = numpy.array([x_axis, phase_data]).T.reshape(-1, 1, 2)
        segments = numpy.concatenate([points[:-1], points[1:]], axis=1)
        lc = LineCollection(segments, cmap=cmap, norm=plt.Normalize(amp_min, amp_max))
        lc.set_array(amp_data)
        lc.set_linewidth(3)
        plt.gca().add_collection(lc)

    gradient_stats(all_gradients)

    plt.xlim(0, duration_max)
    plt.ylim(0, df['event_phase'].max() + 1)

    plt.xlabel('day')
    plt.ylabel('wavenumber '+str(freq)+' phase')
    plt.text(0.95, 0.96, '(b)', transform=ax.transAxes, fontsize='large')


def plot_duration_histogram(ax, df):
    """Plot a bar chart showing the distribution of event duration.
 
    Args:
      ax (AxesSubplot): plot axis
      df (pandas DataFrame): The list of dates
      
    """

    event_data = df['event_number'].values
    event_list = list(event_data)
    duration_list = []
    for event in range(0, event_data.max() + 1):
        event_duration = event_list.count(event)
        duration_list.append(event_duration)

    duration_data = numpy.array(duration_list)

    print 'mean event duration:', duration_data.mean()

    seaborn.distplot(duration_data, kde=False)
    plt.ylabel('frequency')
    plt.xlabel('duration (days)')
    plt.text(0.90, 0.91, '(a)', transform=ax.transAxes, fontsize='large')


def plot_event_summary(df, freq, min_duration, gradient_limit, ofile):
    """Create the event summary plot"""

    fig = plt.figure(figsize=(8, 16))

    ax0 = plt.subplot2grid((4, 2), (0, 0))
    ax1 = plt.subplot2grid((4, 2), (1, 0), rowspan=2, colspan=3)

    plt.sca(ax0)
    plot_duration_histogram(ax0, df)

    plt.sca(ax1)
    filtered_df = df.loc[df['event_duration'] >= min_duration]
    plot_phase_progression(ax1, filtered_df, freq, gradient_limit)

    plt.savefig(ofile, bbox_inches='tight')


def plot_extra_smooth(category, ax, df_subset, phase_freq,
                      bin_centers, valid_min, valid_max,
                      phase_res):
    """Add extra smoothed histogram lines."""

    assert category in ['epochs', 'gradient']

    if category == 'epochs':
        comparison_data = pandas.to_datetime(df_subset['time'].values).year
        bound1 = 1991
        bound2 = 2002
        labels = ['1979-1990', '1991-2002', '2003-2014']
    elif category == 'gradient':
        comparison_data = df_subset['event_gradient'].values
        bound1 = -0.2
        bound2 = 0.2
        labels = ['backwards', 'stationary', 'forward']

    early_bools = comparison_data < bound1
    late_bools = comparison_data > bound2
    mid_bools = numpy.invert(early_bools + late_bools)

    df_subset_early = df_subset.loc[early_bools]
    df_subset_mid = df_subset.loc[mid_bools]
    df_subset_late = df_subset.loc[late_bools]

    ax = plot_kde(ax, df_subset_early[phase_freq].values, bin_centers, 
                  valid_min, valid_max, phase_res,
                  label=labels[0], color=next(palette))
    ax = plot_kde(ax, df_subset_mid[phase_freq].values,bin_centers,
                  valid_min, valid_max, phase_res,
                  label=labels[1], color=next(palette))
    ax = plot_kde(ax, df_subset_late[phase_freq].values, bin_centers, 
                  valid_min, valid_max, phase_res,
                  label=labels[2], color=next(palette))


def plot_phase_distribution(df, phase_freq, freq, phase_res, ofile, 
                            seasonal=False, epochs=False, gradient=False, 
                            start_end=False, ymax=None,
                            phase_groups=None, subset_width=10):
    """Plot a phase distribution histogram."""    
    
    if seasonal:
        season_list = ['DJF', 'MAM', 'JJA', 'SON']
        nrows, ncols = 2, 2
        figure_size = (12, 10)
    else:
        season_list = ['annual']
        nrows, ncols = 1, 1
        figure_size = None

    valid_min = 0.0
    valid_max = (360. / freq) - phase_res
    bin_edge_start = valid_min - (phase_res / 2.0)
    bin_edge_end = valid_max + (phase_res / 2.0)
    bin_edges = numpy.arange(bin_edge_start, bin_edge_end + phase_res, phase_res)
    bin_centers = numpy.arange(valid_min, valid_max + phase_res, phase_res)

    fig = plt.figure(figsize=figure_size)
    for plot_num, season in enumerate(season_list):

        ax = plt.subplot(nrows, ncols, plot_num + 1)
        plt.sca(ax)

        if not season == 'annual':
            months_subset = pandas.to_datetime(df['time'].values).month
            bools_subset = (months_subset == season_months[season][0]) + (months_subset == season_months[season][1]) + (months_subset == season_months[season][2])
            df_subset = df.loc[bools_subset]
        else:
            df_subset = df
        phase_data = df_subset[phase_freq].values

        assert phase_data.min() >= valid_min
        assert phase_data.max() <= valid_max

        first_color = next(palette)

        ax = seaborn.distplot(phase_data, bins=bin_edges, kde=False, color=first_color)
        ax = plot_kde(ax, phase_data, bin_centers, 
                      valid_min, valid_max, phase_res,
                      label='1979-2014', color=first_color, subset_width=subset_width)

        if epochs:
            plot_extra_smooth('epochs', ax, df_subset, phase_freq, 
                              bin_centers, valid_min, valid_max, phase_res) 

        if gradient:
            plot_extra_smooth('gradient', ax, df_subset, phase_freq, 
                              bin_centers, valid_min, valid_max, phase_res) 
    
        if phase_groups:
            for group in phase_groups:
                start, end = group
                plt.axvline(x=start, linestyle='--', color='0.4')
                plt.axvline(x=end, linestyle='--', color='0.4')
    
        ax.set_title(season)
        font = font_manager.FontProperties(size='x-small')
        ax.legend(loc=1, prop=font)
        ax.set_ylabel('Frequency', fontsize='x-small')
        ax.set_xlabel('Longitude', fontsize='x-small')
        ax.set_xlim((bin_edge_start, bin_edge_end))
        if ymax:
            ax.set_ylim((0, ymax))

    fig.savefig(ofile, bbox_inches='tight')


def plot_kde(ax, phase_data, bin_centers,
             lower_bound, upper_bound, 
             phase_res, label,
             color=None, subset_width=None):
    """Plot the kernel density estimate."""

    est = pyqt_fit.kde.KDE1D(phase_data, lower=lower_bound, upper=upper_bound, method=pyqt_fit.kde_methods.cyclic)
    kde_freq = est(bin_centers) * phase_res * len(phase_data)

    ax.plot(bin_centers, kde_freq, label=label, color=color) 

    if subset_width:
        kde_stats(kde_freq, bin_centers, subset_width, label)  

    return ax


def main(inargs):
    """Run program."""

    # Read the data and apply filters
    df = pandas.read_csv(inargs.infile)

    # Create the desired plot
    phase_freq = 'wave%i_phase' %(inargs.freq)
    if inargs.type == 'phase_distribution':
        filtered_df = df.loc[df['event_duration'] >= inargs.min_duration]
        plot_phase_distribution(filtered_df, phase_freq, inargs.freq, inargs.phase_res, inargs.ofile,
                                seasonal=inargs.seasonal, epochs=inargs.epochs, 
                                gradient=inargs.gradient, start_end=inargs.start_end,
                                ymax=inargs.ymax, phase_groups=inargs.phase_group,
                                subset_width=inargs.subset_width)
    elif inargs.type == 'event_summary':
        plot_event_summary(df, inargs.freq, inargs.min_duration, inargs.gradient_limit, inargs.ofile)

    # Sort out metadata
    file_body = inargs.infile.split('.')[0]
    with open (file_body+'.met', 'r') as metfile:
        date_metadata=metfile.read()
    metadata_dict = {inargs.infile: date_metadata}
    gio.write_metadata(inargs.ofile, file_info=metadata_dict)


if __name__ == '__main__':

    extra_info =""" 
example:

author:
    Damien Irving, d.irving@student.unimelb.edu.au

"""

    description='Plot PSA pattern statistics'
    parser = argparse.ArgumentParser(description=description,
                                     epilog=extra_info, 
                                     argument_default=argparse.SUPPRESS,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required data
    parser.add_argument("infile", type=str, help="PSA statistics file from psa_date_list.py")
    parser.add_argument("type", type=str, choices=("phase_distribution", "event_summary"), 
                        help="Desired plot")    
    parser.add_argument("ofile", type=str, help="Output file name")

    # data details
    parser.add_argument("--freq", type=int, default=6, 
                        help="Frequency to use to indicate the wave phase [default: 6]")
    parser.add_argument("--phase_res", type=float, default=None, 
                        help="Phase resolution (e.g. if phase data is deg lon, res is spacing between lons [default: None]")       

    # options that apply to any plot type
    parser.add_argument("--ymax", type=float, default=None, 
                        help="Maximum y axis value for all plots [default: auto]")
    parser.add_argument("--min_duration", type=int, default=0, 
                        help="Minimum event duration [default: 0]")

    # event summary options
    parser.add_argument("--gradient_limit", type=float, default=0.25, 
                        help="Absolute value of limit for defining stationary events [default: 0.25]")
 
    # phase distribution options
    parser.add_argument("--subset_width", type=int, default=None, 
                        help="Print the bounds of the local extrema according to this width [default: None]")
    parser.add_argument("--phase_group", type=float, nargs=2, action='append', default=None, 
                        help="Plot vertical lines to indicate a phase grouping [default: None]")
    parser.add_argument("--seasonal", action="store_true", default=False,
                        help="switch for plotting the 4 seasons for phase distribution plot [default: False]")
    parser.add_argument("--epochs", action="store_true", default=False,
                        help="switch for plotting epoch lines on phase distribution plot [default: False]")
    parser.add_argument("--gradient", action="store_true", default=False,
                        help="switch for plotting gradient lines on phase distribution plot [default: False]")
    parser.add_argument("--start_end", action="store_true", default=False,
                        help="switch for plotting start and end histogram on phase distribution plot [default: False]")

    args = parser.parse_args()            
    main(args)
