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

# ------------------------------------------------------------------------
class WDSFile:

    # --------------------------------------------------------------------
    def __init__(self, file_name):
        bitorder = [1<<x for x in reversed(range(0, 8))]
        with open(file_name, "rb") as f:
            self.bits = [
                True if data & bit else False
                for data in f.read()
                for bit in bitorder
            ]

    # --------------------------------------------------------------------
    def __iter__(self):
        return iter(self.bits)

    # --------------------------------------------------------------------
    def __len__(self):
        return len(self.bits)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
