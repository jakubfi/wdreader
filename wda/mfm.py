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


# ------------------------------------------------------------------------
class MFMData:

    # --------------------------------------------------------------------
    def __init__(self, samples, period, margin, offset):
        self.period = period
        self.margin = margin
        self.offset = offset
        self.samples = samples

    # --------------------------------------------------------------------
    def __iter__(self):
        ticks = []
        ov = -1
        t = 0
        next_clock = self.period

        for v in self.samples:
            # each rising edge restarts clock
            if v and not ov:
                yield (t + self.offset, v)
                next_clock = t + self.period

            # if no rising edge, maybe it's time for the next tick?
            elif t >= next_clock + self.margin:
                yield (next_clock + self.offset, v)
                next_clock = next_clock + self.period

            ov = v
            t += 1


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
