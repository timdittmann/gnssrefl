# -*- coding: utf-8 -*-
"""
"""
import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
from scipy.interpolate import interp1d
import subprocess
import sys
import time

from pathlib import Path
import tiledb

# progress bar for RINEX translation/orbits
from progress.bar import Bar

# my gps libraries
import gnssrefl.gps as g
import gnssrefl.rinpy as rinpy
import gnssrefl.karnak_libraries as k
import gnssrefl.cddis_highrate as ch

# fortran codes for translating RINEX
import gnssrefl.gpssnr as gpssnr
import gnssrefl.gnsssnr as gnsssnr 

import gnssrefl.gnsssnrbigger as gnsssnrbigger

import gnssrefl.gpssnrtdb as gpssnrtdb

class constants:
    omegaEarth = 7.2921151467E-5 #      %rad/sec
    mu = 3.986005e14 # Earth GM value
    c= 299792458 # m/sec
 
#
#
def quickname(station,year,cyy, cdoy, csnr):
    xdir  = os.environ['REFL_CODE'] + '/'
    fname =  xdir + str(year) + '/snr/' + station + '/' + station + cdoy + '0.' + cyy + '.snr' + csnr
    return fname

def run_rinex2snr(station, year_list, doy_list, isnr, orbtype, rate,dec_rate,archive,fortran,nol,overwrite,translator,srate,mk,skipit,stream='R',tdb=False):
    """
    runs the rinex 2 snr conversion
    inputs:
    station name 
    year_list list of years to be analyzed
    doy_list list of doy to be analyzed
    isnr = integer file type choice
    orbtype = 3character orbit type
    rate = high or low
    dec_rate = integer for decimation
    archive = allows you to pick a specific archive
    fortran = boolean, whether you use fortran rinex translators
    nol = boolean for nolook, if set to True, then it will assume RINEX files are in local directory
    overwrite = boolean, make a new SNR file even if one already exists
    translate = string with .... fortran, python, hybrid ??
    srate = sample rate
    mk = makan option
    skipit = skips making files every day, so a value of 7 means weekly.  1 means do every day

    2021feb11, kristine Larson
    translator = fortran, python, or hybrid
    srate - integer sample rate, for RINEX 3 only.
    2021mar20 check for illegal day of years ....
    2021aug01 added mk option for uppercase file names per makan karegar request
    2021aug15 added weekly option
    2021nov08 making nolook work for rinex 3 files ...
    2022feb10 added stream
    2022feb15 added karnak library
    """
    # 
    # do not allow illegal skipit values
    if skipit < 1:
        skipit = 1

    NS = len(station)
    if (NS == 4):
        #print('Assume RINEX 2.11'); 
        version = 2
        if not mk:
            station = station.lower()
    elif (NS == 6 and archive == 'jp') :
        version = 2
        if not mk:
            station = station[-4:].upper()
    elif (NS == 9):
        #print('Assume RINEX 3'); 
        version = 3
        station9ch = station.upper()
        if not mk:
            station = station[0:4].lower()
    else:
        print('Illegal station input - Station must have 4,6,or 9 characters. Exiting')
        sys.exit()
    year_st = year_list[0]
    year_end = year_list[-1]
    doy_st = doy_list[0]
    doy_end = doy_list[-1]
    # 2021 september 12 KL
    # i would like to put this in rinex2snr_cl.py - but I am trying to avoid increasing
    # the workload for the Notebook programmers before the short course.

# this way we are overwriting the doy_list variable
# loop thru years and days 
    for year in year_list:
        ann = g.make_nav_dirs(year)
        cyyyy = str(year)
        dec31 = g.dec31(year)
        if year != year_end:
            doy_en = dec31
        else:
            doy_en = doy_end

        if year == year_st:
            doy_list = list(range(doy_st, doy_en+1,skipit))
        else:
            doy_list = list(range(1, doy_en+1,skipit))

        for doy in doy_list:
            csnr = str(isnr)
            cdoy = '{:03d}'.format(doy) ; cyy = '{:02d}'.format(year-2000)
            # first, check to see if the SNR file exists
            fname =  quickname(station,year,cyy,cdoy,csnr)
            snre = g.snr_exist(station,year,doy,csnr)
            if snre:
                print('SNR file exists', fname)
                if overwrite:
                    #print('you requested it be overwritten, so removing file')
                    subprocess.call(['rm', fname])
                    snre = False
            illegal_day = False
            if (doy > dec31):
                illegal_day = True
                #print('illegal day',illegal_day, doy, dec31)
            # combining these so i don't have to indent everything
            if (not illegal_day) and (not snre):
                r = station + cdoy + '0.' + cyy + 'o'
                rgz = station + cdoy + '0.' + cyy + 'o.gz'
                if nol:
                    print('Will assume RINEX file ', station, ' year:', year, ' doy:', doy, 'is in the local directory')
                    # this assumes RINEX file is in local directory or "nearby"
                    if version == 2:
                        the_makan_option(station,cyyyy,cyy,cdoy) # looks everywhere in your local directories
                        if os.path.exists(r):
                            conv2snr(year, doy, station, isnr, orbtype,rate,dec_rate,archive,fortran,translator, tdb)
                        else:
                            print('You Chose the No Look Option, but did not provide the needed RINEX file.')
                    if version == 3:
                        if rate == 'high':
                            csrate = '01' # high rate assumes 1-sec
                        else:
                            csrate = '{:02d}'.format(srate)
                        streamid = '_' + stream  + '_'
                        # this can be done in a function now ... 
                        r3 = station9ch + streamid + str(year) + cdoy + '0000_01D_' + csrate + 'S_MO.rnx'
                        r3gz = station9ch + streamid + str(year) + cdoy + '0000_01D_' + csrate + 'S_MO.rnx.gz'
                        r2 = station + cdoy + '0.' + cyy + 'o'
                        if os.path.exists(r3gz):
                            subprocess.call(['gunzip', r3gz])
                        if os.path.exists(r3):
                            print('The RINEX 3 file exists locally')
                            fexists = g.new_rinex3_rinex2(r3,r2)
                            if fexists:
                                conv2snr(year, doy, station, isnr, orbtype,rate,dec_rate,archive,fortran,translator, tdb)
                            else:
                                print('Something about the RINEX 3-2 conversion did not work')
                        else:
                            print('You Chose the No Look Option, but did not provide the needed RINEX3 file.')
                            print('I assumed its name was ', r3)

                else:
                    print('Will seek the RINEX file externally')
                    if version == 3:
                        fexists = False
                        rnx_filename = '' # just in  case?
                        print(station9ch, ' year:', year, ' doy:', doy, 'from: ', archive)
                        r2 = station + cdoy + '0.' + cyy + 'o'
                        rinex2exists = False; rinex3name = '';
                        if (rate == 'high'):
                            print('This code only accesses 1-Hz Rinex 3 data at CDDIS')
                            rnx_filename,foundit = ch.cddis_highrate(station9ch, year, doy, 0,stream,dec_rate)
                            #print(rnx_filename, foundit)
                            if foundit:
                                print('The RINEX 3 file has been downloaded. Try to make ', r2)
                                fexists = g.new_rinex3_rinex2(rnx_filename,r2)
                        else:
                            if (archive == 'all'):
                                file_name,foundit = k.universal_all(station9ch, year, doy,srate,stream)
                                if (not foundit): # try again
                                    file_name,foundit = k.universal_all(station9ch, year, doy, srate,k.swapRS(stream))
                            else:
                                file_name,foundit = k.universal(station9ch, year, doy, archive,srate,stream)
                                if (not foundit): # try again
                                    file_name,foundit = k.universal(station9ch, year, doy, archive,srate,k.swapRS(stream))
                            if foundit: # version 3 found - now need to gzip, then hatanaka decompress
                                translated, rnx_filename = go_from_crxgz_to_rnx(file_name)
                            # now make rinex2
                                if translated:
                                    print('The RINEX 3 file has been downloaded. Try to make ', r2)
                                    fexists = g.new_rinex3_rinex2(rnx_filename,r2)
                                    #subprocess.call(['rm', '-f',rnx_filename]) # rnx
                        # this means the rinex 2 version exists
                        if fexists:
                             print('RINEX 2 created from v3', year, doy, ' Now remove RINEX 3 files and convert')
                             subprocess.call(['rm', '-f',rnx_filename]) # rnx
                             conv2snr(year, doy, station, isnr, orbtype,rate,dec_rate,archive,fortran,translator, tdb)
                        else:
                            print('Unsuccessful RINEX 3 retrieval/translation', year, doy)
                    else:
                        print(station, ' year:', year, ' doy:', doy, 'from: ', archive)
                        # this is rinex version 2 - finds rinex and converts it
                        conv2snr(year, doy, station, isnr, orbtype,rate,dec_rate,archive,fortran,translator, tdb)

    #print('And I guess my work is done now!')

def conv2snr(year, doy, station, option, orbtype,receiverrate,dec_rate,archive,fortran,translator,tdb):
    """
    inputs: year and day of year (integers) and station name
    option is for the snr creation ??? integer or character?
    orbtype can be nav or sp3.  if the former, then gpsSNR is used.
    if the later, then gnssSNR
    what are receiverrate and dec_rate defaults?
    this assumes you follow my definitions for where things go,
    i.e. REFL_CODE and ORBITS
    it currently checks Unavco, SOPAC, and SONEL. I should add CDDIS
    author: kristine m. larson
    19may20, added decimation
    19sep12, I got tired of code crashing for files > 20 observables.  I am thus using teqc
    20apr15, xz compression added but also try to streamline it.
    20jul10, added arvchive setting. default is 'all'

    """
    # define directory for the conversion executables
    if not os.path.isdir('logs'):
        subprocess.call(['mkdir', 'logs'])
    logname = 'logs/' + station + '.txt' 
    log = open(logname, 'w+')
    log.write("Receiver rate: {0:5s} \n".format(receiverrate))
    log.write("Decimation rate: {0:3.0f} \n".format(dec_rate))
    log.write("Archive: {0:10s} \n".format(archive))
    log.write("Orbits : {0:10s} \n".format(orbtype))
    exedir = os.environ['EXE']
    snrname_full, snrname_compressed, snre = g.define_and_xz_snr(station,year,doy,option)
    if (snre == True):
        log.write("The snrfile already exists: {0:50s} \n".format(snrname_full))
        print("The snrfile already exists: ", snrname_full)
    else:
        log.write("The snrfile does not exist: {0:50s} \n".format(snrname_full))
        d = g.doy2ymd(year,doy); 
        month = d.month; day = d.day
        # new function to do the whole orbit thing
        foundit, f, orbdir, snrexe = g.get_orbits_setexe(year,month,day,orbtype,fortran) 
        # if you have the orbit file, you can get the rinex file. First lets define the expected names
        print('Orbit file: ', orbdir + '/' + f)
        if foundit:
            # now you can look for a rinex file
            rinexfile,rinexfiled = g.rinex_name(station, year, month, day)
            # This goes to find the rinex file. I am changing it to allow 
            # an archive preference 
            if receiverrate == 'high':
                #g.go_get_rinex_flex(station,year,month,day,receiverrate,archive)
                strip_snr = False # for now - 
                file_name, foundit = k.rinex2_highrate(station, year, doy,archive,strip_snr)
            else:
                # added karnak librariies
                if (archive == 'all'):
                    foundrinex = False
                    for archivechoice in ['unavco','sopac','sonel']:
                        if (not foundrinex):
                            file_name,foundrinex = k.universal_rinex2(station, year, doy, archivechoice)
                else:
                    file_name,foundrinex = k.universal_rinex2(station, year, doy, archive)

                if foundrinex: #uncompress etc  to make o files ...
                    rinexfile, foundit2 = k.make_rinex2_ofiles(file_name) # translate
                    if foundit2:
                        print('SUCCESS', rinexfile)

#           define booleans for various files
            oexist = os.path.isfile(orbdir + '/' + f) == True
            rexist = os.path.isfile(rinexfile) == True
            exc = exedir + '/teqc' 
            texist = os.path.isfile(exc) == True
            if rexist: 
                # decimate using teqc 
                if (texist) and (fortran) and (dec_rate > 0): 
                    log.write("Decimating using teqc:  {0:3.0f}  seconds \n".format(dec_rate))
                    log.write('Unfortunately teqc removes Beidou data. Eventually I will remove this. \n')
                    rinexout = rinexfile + '.tmp'; cdec = str(dec_rate)
                    fout = open(rinexout,'w')
                    subprocess.call([exc, '-O.dec', cdec, rinexfile],stdout=fout)
                    fout.close() # needed?
                    status = subprocess.call(['mv','-f', rinexout, rinexfile])
            # if orbits and rinexfile exist
            if (oexist) and (rexist):
                snrname = g.snr_name(station, year,month,day,option)
                orbfile = orbdir + '/' + f
                #print('translator',translator)
                if translator == 'hybrid':
                    g.make_snrdir(year,station) # make sure output directory exists
                    in1 = g.binary(rinexfile)
                    in2 = g.binary(snrname) # this file is made locally and moved later
                    in3 = g.binary(orbfile)
                    if (len(snrname) > 132) or (len(orbfile) > 132):
                        print('The orbit or SNR file name is too long.')
                        print('Make your environment variable names shorter.')
                        return
                    in4 = g.binary(str(option))
                    if (dec_rate > 0):
                        decr = str(dec_rate)
                    else:
                        decr = '0'
                    in5 = g.binary(decr) # decimation can be used in hybrid option
                    message = 'None '
                    errorlog = 'logs/' + station + '_hybrid_error.txt'
                    in6 = g.binary(errorlog)
                    log.write('SNR file {0:50s} \n will use hybrid of python and fortran to make \n'.format( snrname))
                    # these are calls to the fortran codes that have been ported to be called from python
                    if (orbtype  == 'gps') or (orbtype == 'nav'):
                        if not tdb:
                            gpssnr.foo(in1,in2,in3,in4,in5,in6)
                            print('traditional way')
                        if tdb:
                            print('using tiledb')
                            (iprn, elev, azim, tod, s1, s2, s5) = gpssnrtdb.foo(in1, in2, in3, in4, in5, in6)
                            edot=s6=s7=s8=np.full(len(iprn), np.nan)

                            snr_array = np.stack((iprn, elev, azim, tod, edot, s1, s2, s5, s6,s7,s8), axis=1)
                            #np.save('snr_array.npy',snr_array)
                            tdb_fn = snr2tdb(station, year, doy, snr_array)
                    else:
                        if (orbtype == 'ultra') or (orbtype == 'wum'):
                            print('Using an ultrarapid orbit', orbtype)
                            gnsssnrbigger.foo(in1,in2,in3,in4,in5,in6)
                        else:
                            gnsssnr.foo(in1,in2,in3,in4,in5,in6)
                else:
                    if (translator == 'fortran'):
                        t1=time.time()
                        try:
                            #subprocess.call([snrexe, rinexfile, snrname, orbfile, str(option)])
                            log.write('Using standalone fortran for translation  - separate log is used for stdout \n')
                            flogname = 'logs/' + station + '_fortran.txt'
                            flog = open(flogname, 'w+')
                            a=subprocess.run([snrexe, rinexfile, snrname, orbfile, str(option)],capture_output=True,text=True)
                            ddd = a.stdout; flog.write(ddd); flog.close()
                            status = subprocess.call(['rm','-f', rinexfile ])
                            status = subprocess.call(['xz', orbfile])
                        except:
                            log.write('Problem with making SNR file, check fortran specific log {0:50s} \n'.format(flogname))
                        t2=time.time()
#                        print(' Exec time:', '{0:4.2f}'.format(t2-t1) )
# this is for people that want to use slow python code
                    else:
                        log.write('SNR file {0:50s} \n will use python to make \n'.format( snrname))
                        log.write('Decimating will be done here instead of using teqc \n')
                        t1=time.time()
                        rnx2snr(rinexfile, orbfile,snrname,option,year,month,day,dec_rate,log)
                        t2=time.time()
#                        print(' Exec time:', '{0:4.2f}'.format(t2-t1) )

                # remove the rinex file
                subprocess.call(['rm', '-f',rinexfile])

                if os.path.isfile(snrname): 
#                make sure it exists and is non-zero size before moving it
                    if (os.stat(snrname).st_size == 0):
                        log.write('you created a zero file size which could mean a lot of things \n')
                        log.write('bad exe, bad snr option, do not really have the orbit file \n')
                        status = subprocess.call(['rm','-f', snrname ])
                    else:
                        log.write('A SNR file was created: {0:50s}  \n'.format(snrname_full))
                        print('\n')
                        print('SUCCESS: SNR file was created:', snrname_full)
                        g.store_snrfile(snrname,year,station) 
                else:
                    print('No SNR file was created - check logs section for additional information')
            else:
                print('Either the RINEX file or orbit file does not exist, so there is nothing to convert')
                log.write('Either the RINEX file or orbit file does not exist, so there is nothing to convert \n')
        else:
            print('The orbit file you requested does not exist.')

    # close the log file
    log.close()

    return True

def satorb(week, sec_of_week, ephem):
    """
    inputs are GPS week, seconds of the week, and the appropriate
    ephemeris block from the navigation message
    returns the x,y,z, coordinates of the satellite
    and relativity correction (also in meters), so you add,
    not subtract
    Kristine Larson, April 2017

    """

# redefine the ephem variable
    prn, week, Toc, Af0, Af1, Af2, IODE, Crs, delta_n, M0, Cuc,\
    ecc, Cus, sqrta, Toe, Cic, Loa, Cis, incl, Crc, perigee, radot, idot,\
    l2c, week, l2f, sigma, health, Tgd, IODC, Tob, interval = ephem
    sweek = sec_of_week
    # semi-major axis
    a = sqrta**2
    t = week*7*86400+sweek
    tk = t-Toe
    # no idea if Ryan Hardy is doing this correctly - it should be in a function
    tk  =  (tk - 302400) % (302400*2) - 302400
    n0 = np.sqrt(constants.mu/a**3)
    n = n0+ delta_n
    Mk = M0 + n*tk
    i = 0
    Ek = Mk
    E0 = Mk + ecc*np.sin(Mk)
    # solve kepler's equation
    while(i < 3 or np.abs(Ek-E0) > 1e-12):
        i +=1
        Ek = Mk + ecc*np.sin(E0)
        E0 = Mk + ecc*np.sin(Ek)
    nuk = np.arctan2(np.sqrt(1-ecc**2)*np.sin(Ek),np.cos(Ek)-ecc)
    Phik = nuk + perigee
    duk = Cus*np.sin(2*Phik)+Cuc*np.cos(2*Phik)
    drk = Crs*np.sin(2*Phik)+Crc*np.cos(2*Phik)
    dik = Cis*np.sin(2*Phik)+Cic*np.cos(2*Phik)
    uk = Phik + duk
    rk = a*(1-ecc*np.cos(Ek))+drk

    ik = incl+dik+idot*tk
    xkp = rk*np.cos(uk)
    ykp = rk*np.sin(uk)
    Omegak = Loa + (radot-constants.omegaEarth)*tk -constants.omegaEarth*Toe
    xk = xkp*np.cos(Omegak)-ykp*np.cos(ik)*np.sin(Omegak)
    yk = xkp*np.sin(Omegak)+ykp*np.cos(ik)*np.cos(Omegak)
    zk = ykp*np.sin(ik)
    # try this
    return np.array([xk, yk, zk])


def rnx2snr(obsfile, navfile,snrfile,snroption,year,month,day,dec_rate,log):
    """
    inputs are obsfile - RINEX 2.11
    navfile, which can be nav message or sp3 file
    snrfile: where the results go
    snroption: integer
    year,month,day:  what it sounds like, integer
    dec_rate: integer I think, decimation rate. For fortran users, this is done with teqc

    no output - the output is the snrfile that is created

    This only works for rinex v2.11.  
    Kristine M. Larson August 2020
    This relies on Joakim's rinex reading code
    """
    station = obsfile[0:4]
    #logname = 'logs/' + station + 'python.txt'
    #log = open(logname, 'w+')
    last3 = navfile[-3::]
    # figure out if you have a nav file or a sp3 file
    orbtype = 'sp3' # assume it is sp3
    if (last3 != 'SP3') and (last3 != 'sp3'):
        orbtype = 'nav'
    log.write("Orbit type {0:4s} \n".format(orbtype))
    log.write("File name {0:50s} \n".format(navfile))
    # these are the elevation angle limits I have been using for the various SNR formats
    emin,emax = elev_limits(snroption)

    exitQ = False
    obsdata, systemsatlists, prntoidx, obstypes, header, obstimes,gpstime = rinpy.processrinexfile(obsfile)
    obsdata = rinpy.separateobservables(obsdata, obstypes)
    obslist = obstypes['G'][:] 
    # need to check to see what happens without coordinates
    key = 'APPROX POSITION XYZ' 
    if key in header.keys():
        log.write('Cartesian coordinates are in the RINEX Header \n')
    else:
        log.write('RINEX file does not have station coordinates. Exiting \n')
        print('RINEX file does not have station coordinates. This is illegal. Exiting')
        return
    rv =  header['APPROX POSITION XYZ'] 
    recv = [float(i) for i in rv.split()]
    recv = np.array(recv)
    log.write("XYZ from header {0:15.5f} {1:15.5f} {2:15.5f} \n".format(recv[0],recv[1],recv[2]))
    if np.sum(np.abs(recv)) < 5:
        print('Your receiver coordinates are in the middle of the Earth. Exiting.')
        exitQ = True
        return

    lat, lon, h = g.xyz2llh(recv,1e-8) # returns lat/lon in radians
    up,East,North = g.up(lat,lon) # returns unit vector for UP


# set defaults
    s5exist = False; s1exist = False; s2exist = False;
    if 'S1' in obslist :
        s1exist = True
    if 'S2' in obslist :
        s2exist = True
    if 'S5' in obslist :
        s5exist = True
    if not s1exist and not s2exist: 
        log.write('There are no S1 and no S2 data - this file is not useful for reflectometry \n')
        exitQ = True
    if (orbtype == 'nav'):
        gpssatlist = systemsatlists['G'][:] 
        #print('GPS satellite list', gpssatlist)
        navorbits(navfile,obstimes,obsdata,obslist,prntoidx,gpssatlist,snrfile,s1exist,s2exist,s5exist,up,East,North,emin,emax,recv,dec_rate,log)
    else:
        log.write('Read the sp3 file \n'); sp3 = g.read_sp3file(navfile)
        testing_sp3(gpstime,sp3,systemsatlists,obsdata,obstypes,prntoidx,year,month,day,emin,emax,snrfile,up,East,North,recv,dec_rate,log)
        #test_sp3(gpstime,sp3,systemsatlists,obsdata,obstypes,prntoidx,year,month,day,emin,emax,snrfile,up,East,North,recv,dec_rate,log)

    #print('Closing python RINEX conversion log file:',logname)
    #log.close()

def navorbits(navfile,obstimes,observationdata,obslist,prntoidx,gpssatlist,snrfile,s1exist,s2exist,s5exist,up,East,North,emin,emax,recv,dec_rate,log):
    """
    This is for GPS only files !
    navfile is nav broadcast ephemeris in RINEX format
    inputs are rinex info, obstimes, observationdata,prntoidx,gpssatlist
    various bits about SNR existence
    snrfile is output name
    log is for screen outputs - now going to a file
    """
    log.write('reading the ephemeris data \n')
    ephemdata = g.myreadnav(navfile)
    if len(ephemdata) == 0:
        log.write("Empty ephemeris or the file does not exist \n")
        return

    # change variable name to save typing
    a=obstimes
    if True:
        log.write('Opening output file for the SNR data \n')
        fout = open(snrfile, 'w+')
        K=len(obstimes)
        log.write('Number of epochs in the RINEX file {0:6.0f} \n '.format( K))
        log.write('Decimation rate {0:3.0f} \n'.format(dec_rate))

        with Bar('Processing RINEX', max=K,fill='@',suffix='%(percent)d%%') as bar:
            for i in range(0,K):
                bar.next()
                if np.remainder(i,200) == 0:
                    log.write('Epoch {0:6.0f} \n'.format( i))
            # sod is seconds of the day
                sod = 3600*a[i].hour + 60*a[i].minute + a[i].second
                if dec_rate > 0:
                    rem = sod % dec_rate
                else:
                    rem = 0
                if (rem == 0):
                    gweek, gpss = g.kgpsweek(a[i].year, a[i].month, a[i].day, a[i].hour, a[i].minute, a[i].second)
                    for sat in gpssatlist:
                        s1,s2,s5 = readSNRval(s1exist,s2exist,s5exist,observationdata,prntoidx,sat,i)
                        if (s1 > 0):
                            closest = g.myfindephem(gweek, gpss, ephemdata, sat)
                            if len(closest) > 0:
                                satv = satorb_prop(gweek, gpss, sat, recv, closest)
                                r=np.subtract(satv,recv) # satellite minus receiver vector
                                eleA = g.elev_angle(up, r)*180/np.pi
                                azimA = g.azimuth_angle(r, East, North)
                                if (eleA >= emin) and (eleA <= emax):
                                    fout.write("{0:3.0f} {1:10.4f} {2:10.4f} {3:10.0f} {4:7.2f} {5:7.2f} {6:7.2f} {7:7.2f} {8:7.2f} \n".format(sat,eleA, azimA, sod,0, 0, s1,s2, s5))
        fout.close()
    else:
        log.write('There was some kind of problem with your file, exiting ...\n')
        print('There was some kind of problem with your file, exiting ...')

def readSNRval(s1exist,s2exist,s5exist,observationdata,prntoidx,sat,i):
    """
    what it looks like
    only reads GPS data for now
    interface between Joakim's code and mine ...
    kristine m. larson, july 2019
    """
    s1 = 0; s2 = 0; s5 = 0 # set defaults
    if s1exist:
        s1 = observationdata['G']['S1'][i, prntoidx['G'][sat]]
        if np.isnan(s1):
           s1 = 0
    if s2exist:
        s2 = observationdata['G']['S2'][i, prntoidx['G'][sat]]
        if np.isnan(s2):
            s2 = 0
    if s5exist:
        s5 = observationdata['G']['S5'][i, prntoidx['G'][sat]]
        if np.isnan(s5):
            s5 = 0
    return s1, s2, s5


def satorb_prop(week, secweek, prn, rrec0, closest_ephem):
    """
    Calculates and returns geometric range (in metres) given
    time (week and sec of week), prn, receiver coordinates (cartesian, meters)
    this assumes someone was nice enough to send you the closest ephemeris
    returns the satellite coordinates as well, so you can use htem
    in the A matrix
    Kristine Larson, April 2017
    """
    error = 1

    # might as well start with 70 milliseconds
    SatOrb = satorb(week, secweek-0.07, closest_ephem)
    # first estimate of the geometric range
    geo= g.norm(SatOrb-rrec0)

    deltaT = g.norm(SatOrb - rrec0)/constants.c
    k=0
    #while (error > 1e-8) or (k < 2):
    # should not need more than two iterations, since i am
    #starting with 70 msec
    while (k < 2):
        SatOrb = satorb(week, secweek-deltaT, closest_ephem)
        Th = -constants.omegaEarth * deltaT
        xs = SatOrb[0]*np.cos(Th)-SatOrb[1]*np.sin(Th)
        ys = SatOrb[0]*np.sin(Th)+SatOrb[1]*np.cos(Th)
        SatOrbn = [xs, ys, SatOrb[2]]
        # try this ???
        geo = g.norm(SatOrbn-rrec0)
        deltaT_new = g.norm(SatOrbn-rrec0)/constants.c
        error = np.abs(deltaT - deltaT_new)
        deltaT = deltaT_new
        k += 1
    return SatOrbn


def satorb_prop_sp3(iX,iY,iZ,recv,Tp,ij):
    """
    for satellite number prn
    and receiver coordinates rrec0
    find the x,y,z coordinates at time secweek

    sp3 has the orbit information in it
    """
    # start wit 70 milliseconds as the guess for the transmission time
    nx = iX(Tp[ij]-0.07); ny = iY(Tp[ij]-0.07); nz = iZ(Tp[ij]-0.07)
    oE = constants.omegaEarth
    c = constants.c
    # get initial deltaA
    SatOrb=np.array([nx,ny,nz]).T
    r=np.subtract(SatOrb,recv)
    tau = g.norm(r)/c

    error = 0
    k = 0
    while (k < 2):
        nx = iX(Tp[ij]-tau); ny = iY(Tp[ij]-tau); nz = iZ(Tp[ij]-tau)
        SatOrb=np.array([nx,ny,nz]).T
        Th = -oE * tau
        xs = SatOrb[0]*np.cos(Th)-SatOrb[1]*np.sin(Th)
        ys = SatOrb[0]*np.sin(Th)+SatOrb[1]*np.cos(Th)
        SatOrbn = np.array([xs, ys, SatOrb[2]]).T
        tau=g.norm(SatOrbn-recv)/c
        k+=1

    return SatOrbn

def test_sp3(gpstime,sp3,systemsatlists,obsdata,obstypes,prntoidx,year,month,day, emin,emax,outputfile,up,East,North,recv,dec_rate,log):
    """
    inputs are gpstime( numpy array with week and sow)
    sp3 is what has been read from the sp3 file
    columsn are satNu, week, sow, x, y, z (in meters)
    log is for comments
    """
    checkD = False
    if dec_rate > 0:
        checkD = True
        log.write('You are decimating \n')
    # epoch at the beginning of the day of your RINEX file
    gweek0, gpssec0 = g.kgpsweek(year, month,day,0,0,0 )

    ll = 'quadratic'
#   will store in this variable, then sort it before writing out to a file
    saveit = np.empty(shape=[0,11] )
    fout = open(outputfile, 'w+')
    for con in ['G','E','R','C']:
        if con in obstypes:
            log.write('Good news - found data for constellation {0:s} \n'.format( con))
            obslist = obstypes[con][:]
            satlist = systemsatlists[con][:]
            #print(satlist)
            for prn in satlist:
                addon = g.findConstell(con) # 100,200,or 300 for R,E, and C 
                log.write('Constellation {0:1s} Satellite {1:2.0f}  Addon {2:3.0f} \n'.format( con, prn, addon))
                # window out the data for this satellite
                m = sp3[:,0] == prn + addon
                x = sp3[m,3]
                if len(x) > 0:
                    sp3_week = sp3[m,1] ; sp3_sec = sp3[m,2]
                    x = sp3[m,3] ; y = sp3[m,4] ; z = sp3[m,5]
                # fit the orbits for this satellite
                    t=sp3_sec
                    iX= interp1d(t, x, ll,bounds_error=False,fill_value='extrapolate')
                    iY= interp1d(t, y, ll,bounds_error=False,fill_value='extrapolate')
                    iZ= interp1d(t, z, ll,bounds_error=False,fill_value='extrapolate')
        # get the S1 data for this satellite
                    if 'S1' in obslist:
                        s1 = obsdata[con]['S1'][:, prntoidx[con][prn]]

        # indices when there are no data for this satellite
                    ij = np.isnan(s1)
        # indices when there are data in the RINEX file - this way you do not compute 
        # orbits unless there are data.
                    not_ij = np.logical_not(ij)
                    Tp = gpstime[not_ij,1] # only use the seconds of the week for now
                    s1 = s1[not_ij]; 
                    #print(s1.shape)
                    emp = np.zeros(shape=[len(s1),1],dtype=float)
        # get the rest of the SNR data in a function
                    s2,s5,s6,s7,s8 = extract_snr(prn, con, obslist,obsdata,prntoidx,not_ij,emp)

        # make sure there are no nan values in s2 or s5

                    nepochs = len(Tp)
                    for ij in range(0,nepochs):
                        TT = 0 # default value
                        if checkD:
                            TT = Tp[ij]  % dec_rate # get the modulus
                        if TT == 0:
                            SatOrb = satorb_prop_sp3(iX,iY,iZ,recv,Tp,ij) 
                            r=np.subtract(SatOrb,recv)
                            azimA = g.azimuth_angle(r, East, North)
                            eleA = g.elev_angle(up, r)*180/np.pi
                            # 2021 october 26
                            # thank you to andrea gatti for pointing out the mistake
                            if (eleA >= emin) and (eleA <= emax):
                                fout.write("{0:3.0f} {1:10.4f} {2:10.4f} {3:10.0f} {4:7.2f} {5:7.2f} {6:7.2f} {7:7.2f} {8:7.2f} {9:7.2f} {10:7.2f} \n".format( 
                                    prn+addon,eleA,azimA,Tp[ij]-gpssec0, 0,float(s6[ij]),s1[ij],float(s2[ij]),float(s5[ij]),float(s7[ij]),float(s8[ij]) ))
                                #fout.write("{0:3.0f} {1:10.4f} {2:10.4f} {3:10.0f} {4:7.2f} {5:7.2f} {6:7.2f} {7:7.2f} {8:7.2f} {9:7.2f} {10:7.2f} \n".format( 
                                #    prn+addon,eleA,azimA,Tp[ij]-gpssec0, 0,float(s6[ij]),s1[ij],float(s2[ij]),float(s5[ij]),float(s6[ij]),float(s7[ij]) ))
                else:
                    log.write('This satellite is not in the orbit file. {0:3.0f} \n'.format(prn))
        else:
            log.write('No data for constellation {0:1s} \n'.format(con))
    # print('sort by time')
    # tried saving to variable but it was very slow
    #ne = np.array([prn,eleA,azimA,Tp[ij],0,0,s1[ij],s2[ij],s5[ij],0,0])
    #saveit = np.vstack((saveit,ne))
    #i = np.argsort(saveit[:,3])
    # apply that sort to variable with shorter name
    #s = saveit[i,:]
    log.write('write SNR data to file \n')
    fout.close()


def extract_snr(prn, con, obslist,obsdata,prntoidx,not_ij,emp):
    """
    """
    # defaults are zero arrays
    s2 = emp; s5 = emp; s6 = emp; s7 = emp; s8 = emp
    if 'S2' in obslist:
        s2 = obsdata[con]['S2'][:, prntoidx[con][prn]]
        s2 = s2[not_ij] ; is2 = np.isnan(s2); s2[is2] = 0
    if 'S5' in obslist:
        s5 = obsdata[con]['S5'][:, prntoidx[con][prn]]
        s5 = s5[not_ij]
        is5 = np.isnan(s5); s5[is5] = 0
    if 'S6' in obslist:
        s6 = obsdata[con]['S6'][:, prntoidx[con][prn]]
        s6 = s6[not_ij]
        is6 = np.isnan(s6); s6[is6] = 0
    if 'S7' in obslist:
        s7 = obsdata[con]['S7'][:, prntoidx[con][prn]]
        s7 = s7[not_ij]
        is7 = np.isnan(s7); s7[is7] = 0
    if 'S8' in obslist:
        s8 = obsdata[con]['S8'][:, prntoidx[con][prn]]
        s8 = s8[not_ij]

    return s2,s5,s6,s7,s8

def elev_limits(snroption):
    """
    given Kristine's snr option, return min and max elevation angles
    in degrees
    author: kristine larson
    2020 august 7
    """

    if (snroption == 99):
        emin = 5; emax = 30
    elif (snroption == 50):
        emin = 0; emax = 10
    elif (snroption == 66):
        emin = 0; emax = 30
    elif (snroption == 88):
        emin = 5; emax = 90
    else:
        emin = 5; emax = 30

    return emin, emax

def testit(input):
    """
    """
    print(input)
    return True


def testing_sp3(gpstime,sp3,systemsatlists,obsdata,obstypes,prntoidx,year,month,day, emin,emax,outputfile,up,East,North,recv,dec_rate,log):
    """
    inputs are gpstime( numpy array with week and sow)
    sp3 is what has been read from the sp3 file
    columsn are satNu, week, sow, x, y, z (in meters)
    log is for comments
    """
    checkD = False
    if dec_rate > 0:
        checkD = True
        log.write('You are decimating \n')
    # epoch at the beginning of the day of your RINEX file
    gweek0, gpssec0 = g.kgpsweek(year, month,day,0,0,0 )

    ll = 'quadratic'
#   will store in this variable, then sort it before writing out to a file
    saveit = np.empty(shape=[0,11] )
    fout = open(outputfile, 'w+')
    NsatT = 0
    # make a dictionary for constellation name
    sname ={}; sname['G']='GPS' ; sname['R'] = 'GLONASS'; sname['E'] = 'GALILEO'; sname['C']='BEIDOU'
    for con in ['G','E','R','C']:
        if con in obstypes:
            satL = len(systemsatlists[con][:])
            satS = 'Processing ' + sname[con]
            with Bar(satS, max=satL,fill='@',suffix='%(percent)d%%') as bar:
                log.write('Good news - found data for constellation {0:s} \n'.format( con))
                obslist = obstypes[con][:]
                satlist = systemsatlists[con][:]
                for prn in satlist:
                    bar.next()
                    addon = g.findConstell(con) # 100,200,or 300 for R,E, and C 
                    log.write('Constellation {0:1s} Satellite {1:2.0f}  Addon {2:3.0f} \n'.format( con, prn, addon))
                # window out the data for this satellite
                    m = sp3[:,0] == prn + addon
                    x = sp3[m,3]
                    if len(x) > 0:
                        sp3_week = sp3[m,1] ; sp3_sec = sp3[m,2]
                        x = sp3[m,3] ; y = sp3[m,4] ; z = sp3[m,5]
                # fit the orbits for this satellite
                        t=sp3_sec
                        iX= interp1d(t, x, ll,bounds_error=False,fill_value='extrapolate')
                        iY= interp1d(t, y, ll,bounds_error=False,fill_value='extrapolate')
                        iZ= interp1d(t, z, ll,bounds_error=False,fill_value='extrapolate')
        # get the S1 data for this satellite
                        if 'S1' in obslist:
                            s1 = obsdata[con]['S1'][:, prntoidx[con][prn]]

        # indices when there are no data for this satellite
                        ij = np.isnan(s1)
        # indices when there are data in the RINEX file - this way you do not compute 
        # orbits unless there are data.
                        not_ij = np.logical_not(ij)
                        Tp = gpstime[not_ij,1] # only use the seconds of the week for now
                        s1 = s1[not_ij]; 
                    #print(s1.shape)
                        emp = np.zeros(shape=[len(s1),1],dtype=float)
        # get the rest of the SNR data in a function
                        s2,s5,s6,s7,s8 = extract_snr(prn, con, obslist,obsdata,prntoidx,not_ij,emp)
        # make sure there are no nan values in s2 or s5

                        nepochs = len(Tp)
                        for ij in range(0,nepochs):
                            TT = 0 # default value
                            if checkD:
                                TT = Tp[ij]  % dec_rate # get the modulus
                            if TT == 0:
                                SatOrb = satorb_prop_sp3(iX,iY,iZ,recv,Tp,ij) 
                                r=np.subtract(SatOrb,recv)
                                azimA = g.azimuth_angle(r, East, North)
                                eleA = g.elev_angle(up, r)*180/np.pi
                                if (eleA >= emin) and (eleA <= emax):
                                    # bug reported by Andrea Gatti. 2021 October 26
                                    fout.write("{0:3.0f} {1:10.4f} {2:10.4f} {3:10.0f} {4:7.2f} {5:7.2f} {6:7.2f} {7:7.2f} {8:7.2f} {9:7.2f} {10:7.2f} \n".format( 
                                        prn+addon,eleA,azimA,Tp[ij]-gpssec0, 0,float(s6[ij]),s1[ij],float(s2[ij]),float(s5[ij]),float(s7[ij]),float(s8[ij]) ))
                    else:
                        log.write('This satellite is not in the orbit file. {0:3.0f} \n'.format(prn))
        else:
            log.write('No data for constellation {0:1s} \n'.format(con))
    log.write('write SNR data to file \n')
    fout.close()

                    # only do this for the older version
                    #print('teqc executable exists, will use to eliminate unnecessary observables')
                    #foutname = 'tmp.' + rinexfile
                    #fout = open(foutname,'w')
                    #subprocess.call([exc, '-O.obs','S1+S2+S5+S6+S7+S8', '-n_GLONASS', '27', rinexfile],stdout=fout)
                    #fout.close()
                # store it in the original rinex filename
                    #subprocess.call(['rm','-f',rinexfile])
                    #subprocess.call(['mv','-f',foutname, rinexfile])

def the_makan_option(station,cyyyy,cyy,cdoy):
    """
    this ugly looking code checks a bazillion versions of RINEX versions
    (Z, gz, regular, hatanaka) both in the working directory and in an external rinex area
    $REFL_CODE/rinex/station/year
    
    turns whatever it finds into a regular RINEX file in the working directory
    that file WILL be deleted, but it will not delete those stored externally.
    """
    missing = True
    crnxpath = g.hatanaka_version()  # where hatanaka will be
    r = station + cdoy + '0.' + cyy + 'o'
    rd = station + cdoy + '0.' + cyy + 'd'
    locdir= os.environ['REFL_CODE'] + '/rinex/' + station + '/' + cyyyy + '/'
    # 
    #locdir2= os.environ['RINEX'] + station + '/' + cyyyy + '/'
    #locdir3= os.environ['RINEX'] + station.upper() + '/' + cyyyy + '/'

    print('Will look for files in the working directory and ', locdir)
    # I was testing this ... but have not finished
    #so_many_permutations(r,rd,locdir, crnxpath)

    if os.path.exists(r):
        missing = False

    if os.path.exists(r + '.gz') and missing:
        subprocess.call(['gunzip', r + '.gz'])
        missing = False

    if os.path.exists(r + '.Z') and missing:
        subprocess.call(['uncompress', r + '.Z'])
        missing = False

    if os.path.exists(rd) and missing:
        if os.path.exists(crnxpath):
            subprocess.call([crnxpath,rd])
            subprocess.call(['rm',rd])
            missing = False
        else:
            g.hatanaka_warning(); return

    if os.path.exists(rd + '.gz') and missing:
        subprocess.call(['gunzip', rd + '.gz'])
        if os.path.exists(crnxpath):
            subprocess.call([crnxpath,rd])
            subprocess.call(['rm',rd])
            missing = False
        else:
            g.hatanaka_warning(); 

    if os.path.exists(rd + '.Z') and missing:
        subprocess.call(['uncompress', rd + '.Z'])
        if os.path.exists(crnxpath):
            subprocess.call([crnxpath,rd])
            subprocess.call(['rm',rd])
            missing = False
        else:
            g.hatanaka_warning() 

    if os.path.exists(locdir + r) and missing:
        subprocess.call(['cp', '-f',locdir + r,'.'])
        missing = False

    if os.path.exists(locdir + r + '.gz') and missing:
        subprocess.call(['cp', '-f',locdir + r + '.gz' ,'.'])
        subprocess.call(['gunzip', r + '.gz'])
        missing = False

    if os.path.exists(locdir + r + '.Z') and missing:
        subprocess.call(['cp', '-f',locdir + r + '.Z','.'])
        subprocess.call(['uncompress', r + '.Z'])
        missing = False

    if os.path.exists(locdir + rd) and missing:
        subprocess.call(['cp','-f',locdir + rd,'.'])
        if os.path.exists(crnxpath):
            subprocess.call([crnxpath,rd])
            subprocess.call(['rm',rd])
            missing = False
        else:
            g.hatanaka_warning(); 

    if os.path.exists(locdir + rd + '.Z') and missing:
        subprocess.call(['cp','-f',locdir + rd + '.Z','.'])
        subprocess.call(['uncompress', rd + '.Z'])
        if os.path.exists(crnxpath):
            subprocess.call([crnxpath,rd])
            subprocess.call(['rm',rd])
            missing = False
        else:
            g.hatanaka_warning(); 

    if os.path.exists(locdir + rd + '.gz') and missing:
        subprocess.call(['cp','-f',locdir + rd + '.gz','.'])
        subprocess.call(['gunzip',rd + '.gz'])
        if os.path.exists(crnxpath):
            subprocess.call([crnxpath,rd])
            subprocess.call(['rm',rd])
            missing = False
        else:
            g.hatanaka_warning()

def go_from_crxgz_to_rnx(c3gz):
    """
    sent a gzipped hatanaka file.  gunzip, hatanaka translate
    checks to see if the rnx version exists and returns that
    and the filename
    """
    translated = False # assume failure
    c3 = c3gz[:-3] # crx filename
    rnx = c3.replace('crx','rnx') # rnx filename
    # gunzip
    if os.path.exists(c3gz):
        subprocess.call(['gunzip', c3gz])

    # executable
    crnxpath = g.hatanaka_version()
    if not os.path.exists(crnxpath):
        g.hatanaka_warning()
    else:
        if os.path.exists(c3): # file exists
            subprocess.call([crnxpath,c3])
    if os.path.exists(rnx): # file exists
        translated = True
        print('remove Hatanaka compressed file')
        subprocess.call(['rm','-f',c3])

    return translated, rnx


def make_schema():
    filters1 = tiledb.FilterList([tiledb.ZstdFilter(level=7)])
    filters2 = tiledb.FilterList([tiledb.ByteShuffleFilter(), tiledb.ZstdFilter(level=7)])
    filters3 = tiledb.FilterList([tiledb.BitWidthReductionFilter(), tiledb.ZstdFilter(level=7)])

    d0 = tiledb.Dim(name="time", domain=(315964800000000, 4102444800000000), tile=21600000000, dtype=np.int64,
                    filters=filters1)
    d1 = tiledb.Dim(name="sys", domain=(0, 254), tile=1, dtype=np.uint8, filters=filters1)
    d2 = tiledb.Dim(name="sat", domain=(0, 254), tile=1, dtype=np.uint8, filters=filters1)
    d3 = tiledb.Dim(name="obs", dtype="ascii", filters=filters1)

    dom = tiledb.Domain(d0, d1, d2, d3)

    # Create an attribute
    bit_width_reduction = tiledb.BitWidthReductionFilter()
    compression_zstd = tiledb.ZstdFilter()
    Bzip2 = tiledb.Bzip2Filter(level=9)
    a0 = tiledb.Attr(name="val", dtype=np.float32, filters=filters2)

    # Create the array schema, setting `sparse=True` to indicate a sparse array
    offsets_filters = tiledb.FilterList(
        [tiledb.PositiveDeltaFilter(), tiledb.BitWidthReductionFilter(), tiledb.ZstdFilter(level=7)])
    coords_filters = tiledb.FilterList([tiledb.ZstdFilter(level=7)])
    schema = tiledb.ArraySchema(
        domain=dom, sparse=True, attrs=[a0],
        cell_order='row-major', tile_order='row-major',
        capacity=100000, offsets_filters=offsets_filters,
        coords_filters=coords_filters
    )

    return schema


def unix_time_second_micro(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds() * 1000000


def snr2tdb(station, year, doy, snr_array):
    # remove rows having all zeroes

    iprn_col, elev_col, azim_col, tod_col, edot_col, \
        s1_col, s2_col, s5_col, s6_col, s7_col, s8_col, sys_col= np.arange(12)

    #snr_array = snr_array[~np.all(snr_array == 0, axis=1)]
    snr_array = snr_array[~np.all(((snr_array == 0) | np.isnan(snr_array)), axis=1)]

    # create sys column
    sys = np.zeros((len(snr_array[:, iprn_col]), 1))
    sys[snr_array[:, iprn_col] > 100] = 1
    sys[snr_array[:, iprn_col] > 200] = 2
    snr_array = np.hstack([snr_array, sys])

    #np.save('snr_array.npy', snr_array)
    # sort array (do this in the read instead)
    #ind = np.lexsort((snr_array[:, iprn_col], snr_array[:, sys_col], snr_array[:, tod_col]))
    #snr_array = snr_array[ind]

    #np.save('snr_array2.npy', snr_array)

    # translate time to Time stamp for a given epoch in POSIX Microseconds from 1970-01-01T00:00:00
    file_date = g.doy2ymd(year, doy)
    start = np.int64(unix_time_second_micro(file_date))
    snr_array[:, tod_col] = (snr_array[:, tod_col] * 1e6 + start).astype(int)

    # set dimensional arrays
    d_time_data = snr_array[:, tod_col].astype('int64')
    d_sys_data = snr_array[:, sys_col].astype('uint8')
    d_sat_data = snr_array[:, iprn_col].astype('uint8')

    tdb_fn = "%s.tdb" % station

    obs_list = ['az', 'el', 'edot','s1', 's2', 's5', 's6', 's7', 's8']
    obs_col = [azim_col,elev_col, edot_col, s1_col, s2_col, s5_col, s6_col, s7_col, s8_col]

    if not Path(tdb_fn).exists():
        # if not, make it
        schema1 = make_schema()
        tiledb.Array.create(tdb_fn, schema1)

    with tiledb.open(tdb_fn, 'w') as A:
        for obs, col in zip(obs_list, obs_col):
            d_obs_data = (np.full(d_sys_data.shape, obs))
            a_val_data = snr_array[:, col].astype('float32')
            A[d_time_data, d_sys_data, d_sat_data, d_obs_data] = \
                {'val': a_val_data}
    tiledb.consolidate(tdb_fn)
    tiledb.vacuum(tdb_fn)
    return tdb_fn
'''
OLD VERSION< KEEP FOR NOW

def make_schema():
    filters1 = tiledb.FilterList([tiledb.ZstdFilter(level=7)])
    filters2 = tiledb.FilterList([tiledb.ByteShuffleFilter(), tiledb.ZstdFilter(level=7)])
    filters3 = tiledb.FilterList([tiledb.BitWidthReductionFilter(), tiledb.ZstdFilter(level=7)])

    d0 = tiledb.Dim(name="time", domain=(315964800000000, 4102444800000000), tile=21600000000, dtype=np.int64,
                    filters=filters1)
    d1 = tiledb.Dim(name="sys", domain=(0, 254), tile=1, dtype=np.uint8, filters=filters1)
    d2 = tiledb.Dim(name="sat", domain=(0, 254), tile=1, dtype=np.uint8, filters=filters1)
    d3 = tiledb.Dim(name="obs", dtype="ascii", filters=filters1)

    dom = tiledb.Domain(d0,d1,d2,d3)

    # Create an attribute
    bit_width_reduction = tiledb.BitWidthReductionFilter()
    compression_zstd = tiledb.ZstdFilter()
    Bzip2=tiledb.Bzip2Filter(level=9)
    a0 = tiledb.Attr(name="cn0", dtype=np.float32, filters=filters2)
    a1 = tiledb.Attr(name="elevation", dtype=np.float32, filters=filters2)
    a2 = tiledb.Attr(name="azimuth", dtype=np.float32, filters=filters2)
    a3 = tiledb.Attr(name="edot", dtype=np.float32, filters=filters2)

    # Create the array schema, setting `sparse=True` to indicate a sparse array
    offsets_filters = tiledb.FilterList([tiledb.PositiveDeltaFilter(), tiledb.BitWidthReductionFilter(), tiledb.ZstdFilter(level=7)])
    coords_filters = tiledb.FilterList([tiledb.ZstdFilter(level=7)])
    schema = tiledb.ArraySchema(
        domain=dom, sparse=True, attrs=[a0, a1, a2, a3],
        cell_order='row-major', tile_order='row-major',
        capacity=100000, offsets_filters=offsets_filters,
        coords_filters=coords_filters
    )

    return schema

def snr2tdb(station, year, doy, snr_array):
    # remove rows having all zeroes
    snr_array = snr_array[~np.all(snr_array == 0, axis=1)]

    # create sys column
    sys=np.zeros((len(snr_array[:,0]),1))
    sys[snr_array[:,0]>100]=1
    sys[snr_array[:,0]>200]=2
    snr_array=np.hstack([snr_array,sys])

    #sort array
    ind = np.lexsort((snr_array[:,0],snr_array[:,7],snr_array[:,3]))
    snr_array=snr_array[ind]

    # translate time to Time stamp for a given epoch in POSIX Microseconds from 1970-01-01T00:00:00
    file_date=g.doy2ymd(year,doy)
    start = np.int64(unix_time_second_micro(file_date))
    snr_array[:,3]=(snr_array[:,3]*1e6+start).astype(int)

    # set dimensional arrays
    d_time_data=snr_array[:,3].astype('int64')
    d_sys_data=snr_array[:,7].astype('uint8')
    d_sat_data=snr_array[:,0].astype('uint8')

    # make attribute arrays
    a_el_data=snr_array[:,1].astype('float32')
    a_az_data=snr_array[:,2].astype('float32')
    #a_edot_data=snr_array[:,X]  WHERE DOES EDOT GET POPULATED?
    a_edot_data=np.zeros((len(snr_array[:,0]))).astype('float32')

    tdb_fn="%s.tdb" %station

    obs_list=['s1','s2','s5']

    if not Path(tdb_fn).exists():
        # if not, make it
        schema1=make_schema()
        tiledb.Array.create(tdb_fn, schema1)

    with tiledb.open(tdb_fn, 'w') as A:
        for i,obs in enumerate(obs_list):
            d_obs_data=(np.full(d_sys_data.shape,obs))
            a_cn0_data=snr_array[:,i+4].astype('float32')
            A[d_time_data, d_sys_data, d_sat_data, d_obs_data] = \
                {'cn0': a_cn0_data, 'elevation': a_el_data, 'azimuth': a_az_data, 'edot':a_edot_data}
    tiledb.consolidate(tdb_fn)
    tiledb.vacuum(tdb_fn)
    return tdb_fn

'''
