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
from track import *
from mfm import *

# ------------------------------------------------------------------------
def process_file(file_name):

    track = Track(file_name, MFMClockGen(11, 2, 0), SectorMERA, 17, 512)
    track.analyze()

    # write track image to a file
    with open(file_name.replace(".wds", ".img"), "wb") as outf:
        for sector in track:
            outf.write(bytes(sector))

    print("{}: clock period: {:.4f} samples, {} sectors".format(
        re.sub(".*/", "", file_name),
        track.data.period(),
        len(track)
    ))


# ------------------------------------------------------------------------
# ---- MAIN --------------------------------------------------------------
# ------------------------------------------------------------------------

if len(sys.argv) != 2:
    print("Usage: wda2.py <filename.wds>")
    sys.exit(1)

file_name = sys.argv[1]

process_file(file_name)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
