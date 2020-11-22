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

from wdsfile import *


# ------------------------------------------------------------------------
class MFMData:

    # --------------------------------------------------------------------
    def __init__(self, wds_file_name, period, margin, offset):
        self.period = period
        self.margin = margin
        self.offset = offset
        self.samples = WDSFile(wds_file_name)
        self.data = self.clock_gen()

    # --------------------------------------------------------------------
    def get_period(self):
        return len(self.samples) / len(self.data)

    # --------------------------------------------------------------------
    def __iter__(self):
        return iter(self.data)

    # --------------------------------------------------------------------
    def __len__(self):
        return len(self.data)

    # --------------------------------------------------------------------
    def clock_gen(self):
        ticks = []
        ov = -1
        t = 0
        last_clock = -100

        for v in self.samples:

            # a) each rising edge restarts clock
            # b) if not rising edge, maybe it's time for next tick?
            if ((v == 1) and (ov == 0)) or (t >= last_clock + self.period):
                if (t - last_clock) <= self.margin:
                    ticks.pop()

                ticks.append((t + self.offset, v))
                last_clock = t

            ov = v
            t += 1

        return ticks


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
