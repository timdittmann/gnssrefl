# -*- coding: utf-8 -*-
"""
command line tool for the rinex2snr module
pretty much what it sounds like - it translates rinex files and makes SNR files
kristine larson
2021aug01 added mk option for uppercase file names

compile the fortran first
f2py -c -m gnssrefl.gpssnr gnssrefl/gpssnr.f

2022feb15 added karnak_sub for rinex3
"""

import argparse
import os
import sys

import gnssrefl.gps as g
import gnssrefl.rinex2snr as rnx

from gnssrefl.utils import validate_input_datatypes, str2bool


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("doy", help="start day of year", type=int)
    # optional arguments
    parser.add_argument("-snr", default=None, help="snr file ending", type=int)
    parser.add_argument("-orb", default=None, type=str,
                        help="orbit type, gps, gps+glo, gnss, rapid or you can specify nav,igs,igr,jax,gbm,grg,wum,gfr,ultra")
    parser.add_argument("-rate", default=None, metavar='low', type=str, help="sample rate: low or high")
    parser.add_argument("-dec", default=None, type=int, help="decimate (seconds)")
    parser.add_argument("-nolook", default=None, metavar='False', type=str,
                        help="True means only use RINEX files on local machine")
    parser.add_argument("-fortran", default=None, metavar='False', type=str,
                        help="True means use Fortran RINEX translators ")
    parser.add_argument("-archive", default=None, metavar='all',
                        help="specify one archive: unavco,sopac,cddis,sonel,nz,ga,ngs,bkg,nrcan,jp", type=str)
    parser.add_argument("-doy_end", default=None, help="end day of year", type=int)
    parser.add_argument("-year_end", default=None, help="end year", type=int)
    parser.add_argument("-overwrite", default=None, help="boolean", type=str)
    parser.add_argument("-translator", default=None, help="translator(fortran,hybrid,python)", type=str)
    parser.add_argument("-samplerate", default=None, help="sample rate in sec (RINEX 3 only)", type=int)
    parser.add_argument("-stream", default=None, help="Set to R or S (RINEX 3 only)", type=str)
    parser.add_argument("-mk", default=None, help="use True for uppercase station names ", type=str)
    parser.add_argument("-weekly", default=None, help="use True for weekly data translation", type=str)
    parser.add_argument("-tdb", default=None, metavar='False', help="boolean", type=str)

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['nolook', 'fortran', 'overwrite', 'mk', 'weekly','tdb']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def rinex2snr(station: str, year: int, doy: int, snr: int = 66, orb: str = 'nav', rate: str = 'low', dec: int = 0,
              fortran: bool = False, nolook: bool = False, archive: str = 'all', doy_end: int = None,
              year_end: int = None, overwrite: bool = False, translator: str = 'hybrid', samplerate: int = 30,
              stream: str = 'R', mk: bool = False, weekly: bool = False, tdb: bool = False):
    """
        rinex2snr translates RINEX files to an SNR format. This function will fetch orbit files for you.

        Parameters:
        ___________
        station : string
            4 or 9 character ID of the station

        year : integer
            Year

        doy : integer
            Day of year

        snr : integer, optional
            SNR format. This tells the code what elevation angles to save data for. Will be the snr file ending.
            value options:
                66 (default) : saves all data with elevation angles less than 30 degrees
                99 : saves all data with elevation angles between 5 and 30 degrees
                88 : saves all data with elevation angles between 5 and 90 degrees
                50 : saves all data with elevation angles less than 10 degrees

        orb : string, optional
            Which orbit files to download.
            value options:
            gps (default) : will use GPS broadcast orbit
            gps+glos : will use JAXA orbits which have GPS and Glonass (usually available in 48 hours)
            gnss : will use GFZ orbits, which is multi-GNSS (available in 3-4 days?)
            nav : GPS broadcast, perfectly adequate for reflectometry.
            igs : IGS precise, GPS only
            igr : IGS rapid, GPS only
            jax : JAXA, GPS + Glonass, within a few days, missing block III GPS satellites
            gbm : GFZ Potsdam, multi-GNSS, not rapid
            grg : French group, GPS, Galileo and Glonass, not rapid
            esa : ESA, multi-GNSS
            gfr : GFZ rapid, GPS, Galileo and Glonass, since May 17 2021
            wum : (disabled) Wuhan, multi-GNSS, not rapid

        rate : string, optional
            The data rate
            value options:
                low (default) : standard rate data
                high : high rate data

        dec : integer, optional
            Decimation rate. 0 is default.

        fortran : boolean, optional
            Whether to use fortran to translate the rinex files. Note: This option requires Fortran RINEX translators.
            Please see documentation at https://github.com/kristinemlarson/gnssrefl to see instructions to get these.
            value options:
                False (default) : does not use fortran to translate rinex
                True : uses fortran to translate rinex

        nolook : boolean, optional
            This parameter tells the code not to get the rinex files online if the files exist locally already.
            default is False.

        archive : string, optional
            Select which archive to get the files from.
            Default is None. None means that the code will search and find an archive with the data for you.
                value options:
                unavco
                sonel (global sea level observing system)
                sopac (Scripps Orbit and Permanent Array Center)
                cddis
                ngs (National Geodetic Survey)
                nrcan (Natural Resources Canada)
                bkg (German Agency for Cartography and Geodesy)
                nz (GNS, New Zealand)
                ga (Geoscience Australia)
                bev (Austria Federal Office of Metrology and Surveying)

        doy_end : int, optional
            end day of year. This is to create a range from doy to doy_end of days to get the snr files.
            If year_end parameter is used - then day_end will end in the day of the year_end.
            Default is None. (meaning only a single day using the doy parameter)

        year_end : int, optional
            end year. This is to create a range from year to year_end to get the snr files for more than one year.
            Default is None.

        overwrite : boolean, optional
            Make a new SNR file even if one already exists (overwrite existing file).
            Default is False.

        translator : string, optional
            hybrid (default) : uses a combination of python and fortran to translate the files.
            fortran : uses fortran to translate (requires the fortran translator executable - see https://github.com/kristinemlarson/gnssrefl)
            python : uses python to translate. (Warning: This can be very slow)

        srate : int, optional
            sample rate for rinex 3 only
            Default is 30.

        mk : boolean, optional
            The Makan option. Use True for uppercase station names.
            Default is False.

        weekly : boolean, optional
            Takes 1 out of every 7 days in the doy-doy_end range (one file per week) - used to save time.
            Default is False.

        """
    # validate parameter types
    # validate_input_datatypes(rinex2snr, station=station, year=year, doy=doy, snr=snr, orb=orb, rate=rate, dec=dec, fortran=fortran,
    #                nolook=nolook, archive=archive, doy_end=doy_end, year_end=year_end, overwrite=overwrite,
    #                translator=translator, srate=srate, mk=mk, weekly=weekly)

    # make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()
    #
    # rename the user inputs as variables
    #
    ns = len(station)
    if (ns == 4) or (ns == 6) or (ns == 9):
        pass
    else:
        print('Illegal input - Station name must have 4 (RINEX 2), 6 (GSI), or 9 (RINEX 3) characters. Exiting.')
        sys.exit()

    if len(str(year)) != 4:
        print('Year must be four characters long. Exiting.', year)
        sys.exit()

    # currently allowed orbit types - shanghai removed 2020sep08
    # added GFZ rapid, aka gfr 2021May19 but it does not work anymore.  point it to gbm
    #
    # added ESA, thank you to Makan
    orbit_list = ['gps', 'gps+glo', 'gnss', 'nav', 'igs', 'igr', 'jax', 'gbm',
                  'grg', 'wum', 'gfr', 'esa', 'ultra', 'rapid', 'gnss2']
    if orb not in orbit_list:
        print('You picked an orbit type I do not recognize. Here are the ones I allow')
        print(orbit_list)
        print('Exiting')
        sys.exit()

    # if you choose GPS, you get the nav message
    if orb == 'gps':
        orb = 'nav'

    # if you choose ultra , you get the GFZ rapid 
    if orb == 'rapid':
        orb = 'gfr'

    # if you choose GNSS, you get the GFZ sp3 file  (precise)
    if orb == 'gnss':
        orb = 'gbm'

    if orb == 'gnss2':
        # this code wants year month day....
        year, month, day = g.ydoy2ymd(year, doy)
        filename, fdir, foundit = g.avoid_cddis(year, month, day)
        orb = 'gbm'
        if not foundit:
            print('You picked the backup multi-GNSS option.')
            print('I tried to get the file from IGN and failed. Exiting')
            sys.exit()
        else:
            print('found GFZ orbits at IGN - warning, only a single file at a time')

    # if you choose GPS+GLO, you get the JAXA sp3 file 
    if orb == 'gps+glo':
        orb = 'jax'

    # default is to use hybrid for RINEX translator
    if translator is None:
        # the case when someone sets fortran to true and doesn't set translator also
        if fortran is not False:
            translator = 'fortran'
        else:
            translator = 'hybrid'
    elif translator == 'hybrid':
        fortran = False  # override
    elif translator == 'python':
        fortran = False  # override - but this is sllllllooooowwww
    elif translator == 'fortran':
        fortran = True
    translator_accepted = [None, 'fortran', 'hybrid', 'python']
    if translator not in translator_accepted:
        print(f'translator option must be one of {translator_accepted}. Exiting.')
        sys.exit()

    # check that the fortran exe exist
    if fortran:
        if orb == 'nav':
            snrexe = g.gpsSNR_version()
            if not os.path.isfile(snrexe):
                print('You have selected the fortran and GPS only options.')
                print('However, the fortran translator gpsSNR.e has not been properly installed.')
                print('We are changing to the hybrid translator option.')
                fortran = False
                translator = 'hybrid'
        else:
            snrexe = g.gnssSNR_version()
            if not os.path.isfile(snrexe):
                print('You have selected the fortran and GNSS options.')
                print('However, the fortran translator gnssSNR.e has not been properly installed.')
                print('We are changing to the python translator option (the hybrid is not yet working).')
                fortran = False
                translator = 'python'

    # default is set to low.  pick high for 1sec files
    rate = rate.lower()
    rate_accepted = ['low', 'high']
    if rate not in rate_accepted:
        print('rate not set to either "low" or "high". Exiting')
        sys.exit()

    if doy_end is None:
        doy2 = doy
    else:
        doy2 = doy_end

    archive_list_rinex3 = ['unavco', 'cddis', 'bev', 'bkg', 'ga', 'epn', 'all']
    archive_list = ['sopac', 'unavco', 'sonel', 'cddis', 'nz', 'ga', 'bkg', 'jeff',
                    'ngs', 'nrcan', 'special', 'bev', 'jp', 'all']

    # no longer allow all
    highrate_list = ['unavco', 'nrcan', 'cddis']  # cddis is only rinex 2 for now

    if ns == 9:
        # rinex3
        if archive not in archive_list_rinex3:
            print('You have chosen an archive not supported by the code.')
            print(archive_list_rinex3)
            sys.exit()
    else:
        # rinex2
        if rate == 'high':
            if archive not in highrate_list:
                print(f'You have chosen highrate and {archive} but only unavco, cddis and nrcan are allowed. Exiting.')
                print('Please help code up access to additional archives')
                sys.exit()
        else:
            if archive not in archive_list:
                print('You picked an archive that is not allowed. Exiting')
                print(archive_list)
                sys.exit()

    year1 = year
    if year_end is None:
        year2 = year 
    else:
        year2 = year_end

# the weekly option
    skipit = 1
    if weekly:
        print('you have invoked the weekly option')
        skipit = 7

    # change skipit to be sent to rinex2snr.py
    #doy_list = list(range(doy, doy2+1))
    #doy_list = list(range(doy, doy2+1,skipit))
    # this makes the correct lists in the function
    doy_list = [doy, doy2]
    year_list = list(range(year1, year2+1))

    # default is to use hybrid for RINEX translator

    if translator == 'hybrid':
        fortran = False  # override
    if translator == 'python':
        fortran = False  # override - but this is sllllllooooowwww

    if fortran is True:
        translator = 'fortran'

    # the Makan option
    if mk:
        print('You have invoked the Makan option')

    if stream not in ['R', 'S']:
        stream = 'R'

    args = {'station': station, 'year_list': year_list, 'doy_list': doy_list, 'isnr': snr, 'orbtype': orb,
            'rate': rate, 'dec_rate': dec, 'archive': archive, 'fortran': fortran, 'nol': nolook,
            'overwrite': overwrite, 'translator': translator, 'srate': samplerate, 'mk': mk,
            'skipit': skipit, 'stream': stream, 'tdb': tdb}

    rnx.run_rinex2snr(**args)
    print('Feedback written to subdirectory logs')


def main():
    args = parse_arguments()
    rinex2snr(**args)


if __name__ == "__main__":
    main()


