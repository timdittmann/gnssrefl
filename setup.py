from setuptools import setup, find_packages
from numpy.distutils.core import setup, Extension

ext1 = Extension(name='gnssrefl.gpssnr', 
        sources=['gnssrefl/gpssnr.f'], 
        f2py_options=['--verbose'],
        )

ext2 = Extension(name='gnssrefl.gnsssnr', 
        sources=['gnssrefl/gnsssnr.f'], 
        f2py_options=['--verbose'],
        )
ext3 = Extension(name='gnssrefl.gnsssnrbigger', 
        sources=['gnssrefl/gnsssnrbigger.f'], 
        f2py_options=['--verbose'],
        )

ext4 = Extension(name='gnssrefl.gpssnrtdb',
        sources=['gnssrefl/gpssnrtdb.f'],
        f2py_options=['--verbose'],
        )

ext5 = Extension(name='gnssrefl.gnsssnrtdb',
        sources=['gnssrefl/gnsssnrtdb.f'],
        f2py_options=['--verbose'],
        )

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

requirements = ["numpy","wget","scipy","matplotlib","requests","progress","astropy", "tiledb"]

setup(
    name="gnssrefl",
    version="1.1.3",
    author="Kristine Larson",
    author_email="kristinem.larson@gmail.com",
    description="A GNSS reflectometry software package ",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/kristinemlarson/gnssrefl/",
    packages=find_packages(),
    include_package_data=True,
    entry_points ={ 
        'console_scripts': [ 
            'gnssir = gnssrefl.gnssir_cl:main',
            'rinex2snr = gnssrefl.rinex2snr_cl:main',
            'daily_avg = gnssrefl.daily_avg_cl:main',
            'quickLook= gnssrefl.quickLook_cl:main',
            'download_rinex = gnssrefl.download_rinex:main',
            'download_orbits = gnssrefl.download_orbits:main',
            'make_json_input = gnssrefl.make_json_input:main',
            'ymd = gnssrefl.ymd:main',
            'ydoy = gnssrefl.ydoy:main',
            'xyz2llh = gnssrefl.xyz2llh:main',
            'llh2xyz = gnssrefl.llh2xyz:main',
            'prn2gps = gnssrefl.prn2gps:main',
            'download_tides = gnssrefl.download_tides:main',
            'subdaily= gnssrefl.subdaily_cl:main',
            'gpsweek = gnssrefl.gpsweek:main',
            'update_snr_files = gnssrefl.update_snr_files:main',
            'nmea2snr= gnssrefl.nmea2snr_cl:main',
            'installexe= gnssrefl.installexe_cl:main',
            'download_unr = gnssrefl.download_unr:main',
            'query_unr= gnssrefl.query_unr:main',
            'mp1mp2= gnssrefl.computemp1mp2:main',
            'download_teqc = gnssrefl.download_teqc:main',
            'rinex3_rinex2= gnssrefl.rinex3_rinex2:main',
            'veg_multiyr= gnssrefl.veg_multiyr:main',
            'check_rinex= gnssrefl.check_rinex:main',
            'rinex3_snr= gnssrefl.rinex3_snr:main',
            'filesizes= gnssrefl.filesizes:main',
            'invsnr= gnssrefl.invsnr_cl:main',
            'invsnr_input= gnssrefl.invsnr_input:main',
            ], 
        },
    install_requires=requirements,
    ext_modules = [ext1,ext2,ext3,ext4,ext5],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
