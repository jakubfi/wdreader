#  Copyright (c) 2013, 2020, 2023 Jakub Filipowicz <jakubf@gmail.com>
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

from mfm import *
from sector import *

# ------------------------------------------------------------------------
class Track:

    # --------------------------------------------------------------------
    def __init__(self, mfm_data, sector_class, sectors_per_track, verbosity=0):
        self.data = mfm_data
        self.sector_class = sector_class
        self.sectors_per_track = sectors_per_track
        self.sectors = {}
        self.verbosity = verbosity

    # --------------------------------------------------------------------
    def analyze(self):
        sector = self.sector_class()
        ret = True
        for s in self.data:
            res = sector.feed(s)

            if res == State.DONE:
                crc_head = "OK" if sector.head_crc_ok else "FAILED"
                crc_data = "OK" if sector.data_crc_ok else "FAILED"
                status = "FAILED" if sector.bad else "OK"
                if not sector.head_crc_ok or not sector.data_crc_ok or sector.bad:
                    ret = False
                if not sector.head_crc_ok or not sector.data_crc_ok or sector.bad or self.verbosity > 1:
                    print(f" * Sector {sector.cylinder}/{sector.head}/{sector.sector:2}: CRC header: {crc_head}, CRC data: {crc_data}, status: {status}")

                self.sectors[sector.sector] = sector
                if len(self.sectors) == self.sectors_per_track:
                    break
                else:
                    sector = self.sector_class()

            elif res == State.FAILED:
                print(" * Cooking sector failed")
                break

        return ret

    # --------------------------------------------------------------------
    def sector(self, num):
        return self.sectors[num]

    # --------------------------------------------------------------------
    def __len__(self):
        return len(self.sectors)

    # --------------------------------------------------------------------
    def __iter__(self):
        return iter(self.sectors.items())

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
