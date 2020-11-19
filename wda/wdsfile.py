#  Copyright (c) 2013 Jakub Filipowicz <jakubf@gmail.com>
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
class WDSFile:

    # --------------------------------------------------------------------
    def __init__(self, wds_file_name):
        wds_f = open(wds_file_name, "rb")
        self.data = wds_f.read()
        wds_f.close()

        self.bits = []
        self.extract()

    # --------------------------------------------------------------------
    def extract(self):
        bitorder = [x for x in reversed(range(0, 8))]
        self.bits = [
            (b >> pos) & 1
            for b in self.data
            for pos in bitorder
        ]

    # --------------------------------------------------------------------
    def __iter__(self):
        return iter(self.bits)

    # --------------------------------------------------------------------
    def __len__(self):
        return len(self.bits)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
