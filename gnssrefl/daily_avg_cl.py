# command line module that calls daily_avg.py
import argparse
import matplotlib.pyplot as matplt
import os
import sys

# my code
import gnssrefl.gps as g
import gnssrefl.daily_avg as da

from gnssrefl.utils import str2bool

def parse_arguments():
    # must input start and end year
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name (4 ch only)", type=str)
    parser.add_argument("medfilter", help="Median filter for daily RH (m). Start with 0.25 ", type=float)
    parser.add_argument("ReqTracks", help="required number of tracks", type=int)
    parser.add_argument("-txtfile", default=None, type=str, help="Set your own output filename")
    parser.add_argument("-plt", default=None, type=str, help="plt to screen: True or False")
    parser.add_argument("-extension", default=None, type=str, help="extension for solution names")
    parser.add_argument("-year1", default=None, type=int, help="restrict to years starting with")
    parser.add_argument("-year2", default=None, type=int, help="restrict to years ending with")
    parser.add_argument("-fr", default=0, type=int, help="frequency, default is to use all")
    parser.add_argument("-csv", default=None, type=str, help="True if you want csv instead of plain text")
    parser.add_argument("-azim1", default=None, type=int, help="minimum azimuth (deg)")
    parser.add_argument("-azim2", default=None, type=int, help="maximum azimuth (deg)")
    parser.add_argument("-test", default=None, type=str, help="augmentation to plot")
    parser.add_argument("-subdir", default=None, type=str, help="non-default subdirectory for output ")
    parser.add_argument("-offset_meta", default=None, type=str, help="True if you want to check earthscope/gage offset meta")
    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['plt', 'csv','test','offset_meta']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def daily_avg(station: str , medfilter: float, ReqTracks: int, txtfile: str = None, plt: bool = True, 
        extension: str = '', year1: int = 2005, year2: int = 2030, fr: int = 0, csv: bool = False, azim1: int = 0,
              azim2: int = 360, test: bool = False, subdir: str=None, offset_meta: bool = False):
    """
        Parameters
        ----------
        station : string
            4 ch station name 

        medfilter : float
            Median filter for daily reflector height (m). Start with 0.25 for surfaces where you expect no significant 
            subdaily change (snow/lakes).

        ReqTracks : int
            Required number of daily satellite tracks to save the daily average value.

        txtfile : str, optional
            Use this parameter to set your own output filename.
            default is to let the code choose.

        plt : bool, optional
            whether to print plots to screen or not.
            default is True.

        extension : str, optional
            extension for solution names.
            default is ''. (empty string)

        year1 : int, optional
            restrict to years starting with.
            default is 2005.

        year2 : int, optional
            restrict to years ending with.
            default is 2030.

        fr : int, optional
            GNSS frequency. Value options:
                0 (default) : all

                1 : GPS L1

                2 : GPS L2

                20 : GPS L2C

                5 : GPS L5

                101 : GLONASS L1

                102 : GLONASS L2

                201 : GALILEO E1

                205 : GALILEO E5a

                206 : GALILEO E6

                207 : GALILEO E5b

                208 : GALILEO E5

                302 : BEIDOU B1

                306 : BEIDOU B3

                307 : BEIDOU B2

        csv : boolean, optional
            Whether you want csv instead of a plain text file.
            default is False.

        azim1 : int, optional
            minimum azimuth, degrees
            note: should be modified to allow negative azimuth

        azim2 : int, optional
            maximum azimuth, degrees

        test : bool
            augmentations to the plot

        subdir: str
            non-default subdirectory for Files output

    """
    if len(station) != 4:
        print('Station names must have four characters. Exiting.')
        sys.exit()

    plt2screen = plt # since variable was originally this name 
    # make sure environment variables are set
    g.check_environ_variables()
    if subdir == None:
        subdir = station
    g.set_subdir(subdir)
# where the summary files will be written to
    xdir = os.environ['REFL_CODE']
    txtdir = xdir + '/Files/'  + subdir


    # set the name of the output format
    if csv:
        alldatafile = txtdir + '/' + station + '_allRH.csv' 
    else:
        alldatafile = txtdir + '/' + station + '_allRH.txt' 

    tv, obstimes = da.readin_plot_daily(station, extension, year1, year2, fr, alldatafile, csv, medfilter, ReqTracks,azim1,azim2,test,subdir,offset_meta)

    # default is to show the plots
    if plt2screen:
        matplt.show()

    # now write out the result file:

    if txtfile is None:
        if csv:
            outfile = txtdir + '/' + station + '_dailyRH.csv' 
        else:
        # use default  filename for the average
            outfile = txtdir + '/' + station + '_dailyRH.txt' 
    else:
        # use filename provided by the user
        outfile = txtdir + '/' + txtfile

    da.write_out_RH_file(obstimes, tv, outfile, csv)


def main():
    args = parse_arguments()
    daily_avg(**args)


if __name__ == "__main__":
    main()
