#!/usr/bin/env python3

#  Copyright (c) 2013, 2020 Jakub Filipowicz <jakubf@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import sys
import re
import argparse
from wdsfile import *
from track import *
from mfm import *


parser = argparse.ArgumentParser()
parser.add_argument('track', nargs=1, help='track to analyze')
parser.add_argument("-f", "--format", help="sector format", required=True)
parser.add_argument("-s", "--sectors", help="sectors per track", required=True, type=int)
parser.add_argument("-c", "--clock", help="base clock period (samples)", default=11, type=int)
parser.add_argument("-m", "--margin", help="clock search margin (samples)", default=2, type=int)
parser.add_argument("-o", "--offset", help="clock offset (samples)", default=0, type=int)
parser.add_argument('-v', '--verbose', action='store_true', default=False)
args = parser.parse_args()

file_name = args.track[0]
short_fname = re.sub(".*/", "", file_name)
sector_class = globals()[args.format]

if args.verbose:
    print(f"Processing file: {short_fname}")

samples = WDSFile(file_name)
mfm_data = MFMData(samples, period=args.clock, margin=args.margin, offset=args.offset)
track = Track(mfm_data, sector_class, args.sectors)
track.analyze()

with open(file_name.replace(".wds", ".img"), "wb") as outf:
    for i in range(0, args.sectors):
        try:
            outf.write(bytes(track.sector(i)))
        except KeyError:
            print(f" * Sector {i} missing in {file_name}")
            # fill with dummy data
            outf.write(bytes(256 * [0xff, 0]))


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
