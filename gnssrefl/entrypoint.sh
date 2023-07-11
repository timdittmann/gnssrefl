#!/bin/sh
# Copy data into a possibly-mounted location
cp -a /usr/src/gnssrefl/gnssrefl/gpt_1wA.pickle /etc/gnssrefl/refl_code/input/
cp -a /usr/src/gnssrefl/gnssrefl/station_pos.db /etc/gnssrefl/refl_code/Files/
# Then run the image's CMD
exec "$@"