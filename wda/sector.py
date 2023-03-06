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

import crc_algorithms

# ------------------------------------------------------------------------
class State:
    FAILED = 0
    COOKING = 1
    DONE = 2
    LOOP_END = 3


# ------------------------------------------------------------------------
class Looper:

    # -------------------------------------------------------------------
    def __init__(self):
        self.name = "Loop End"

    # -------------------------------------------------------------------
    def feed(self, s):
        return State.LOOP_END

    # -------------------------------------------------------------------
    def last(self, bit):
        pass


# ------------------------------------------------------------------------
class Skipper:

    # -------------------------------------------------------------------
    def __init__(self, name, hbit_count):
        self.name = name
        self.hbit_count = hbit_count
        self.counter = 0

    # -------------------------------------------------------------------
    def feed(self, s):
        self.counter += 1

        if self.counter >= self.hbit_count:
            self.counter = 0
            return State.DONE
        else:
            return State.COOKING

    # -------------------------------------------------------------------
    def last(self, bit):
        pass


# ------------------------------------------------------------------------
class BitSeqFinder:

    # -------------------------------------------------------------------
    def __init__(self, name, hbit_seq, deadline, callback):
        self.name = name
        self.hbit_seq = hbit_seq
        self.deadline = deadline
        self.callback = callback

        self.hbit_buf = []
        self.clock_tick = 0

    # --------------------------------------------------------------------
    def feed(self, s):
        (t, v) = s
        self.hbit_buf.append(v)

        # past the deadline
        if self.clock_tick > (self.deadline + len(self.hbit_seq)):
            self.hbit_buf = []
            self.clock_tick = 0
            print(" * Could not find bit sequence within given deadline")
            return State.FAILED

        # buffer full
        elif len(self.hbit_buf) == len(self.hbit_seq):
            # does it match?
            if self.hbit_buf == self.hbit_seq:
                self.hbit_buf = []
                self.clock_tick = 0
                self.callback(self.hbit_buf)
                return State.DONE
            else:
                self.hbit_buf.pop(0)

        self.clock_tick += 1

        return State.COOKING

    # -------------------------------------------------------------------
    def last(self, bit):
        pass


# ------------------------------------------------------------------------
class ByteReader:

    # --------------------------------------------------------------------
    def __init__(self, name, byte_count, callback):
        self.name = name
        self.byte_count = byte_count
        self.callback = callback
        self.bytes = [0]
        self.byte_pos = 0
        self.bit_pos = 7
        self.bit_odd = 1
        self.last_bit = -1
        self.clock = 0

    # --------------------------------------------------------------------
    def feed(self, s):
        (t, v) = s

        # skip odd bits (clock)
        if self.bit_odd:
            self.clock = v
            self.bit_odd = 0
            return State.COOKING

        self.bit_odd = 1

        # check for illegal MFM bits
        if (v == 1) and (self.clock == 1):
            print(" * MFM illegal cell: 11 at sample: {}".format(t))
        elif v == 0:
            if (self.clock == 0) and (self.last_bit == 0):
                print(" * MFM illegal cell: 00 after 0 at sample: {}".format(t))
            elif (self.clock == 1) and (self.last_bit == 1):
                print(" * MFM illegal cell: 10 after 1 at sample: {}".format(t))

        # shift in even bits (data)
        self.bytes[self.byte_pos] |= (v << self.bit_pos)
        self.last_bit = v

        self.bit_pos -= 1

        # byte is done
        if self.bit_pos < 0:
            self.byte_pos += 1
            if self.byte_pos == self.byte_count:
                self.callback(self.bytes)
                self.byte_pos = 0
                self.bit_pos = 7
                self.bytes = [0]
                self.bit_odd = 1
                return State.DONE
            else:
                self.bit_pos = 7
                self.bytes.append(0)
                return State.COOKING

    # -------------------------------------------------------------------
    def last(self, bit):
        self.last_bit = bit


# --------------------------------------------------------------------
class MFMSector:

    A1 = [0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1]
    SYNC = [1, 0] * (10*8)

    # --------------------------------------------------------------------
    def __init__(self, sector_size):
        self.sector_size = sector_size

        self.last_bit = 0
        self.crc_head_buf = []
        self.crc_data_buf = []
        self.crc16_alg = None
        self.crc32_alg = None
        self.cylinder = 0
        self.head = 0
        self.sector = 0
        self.sector_size = 0
        self.bad = False

        self.head_crc_ok = False
        self.data_crc_ok = False

        self.data = []

        self.phase = 0
        self.layout = []

    # --------------------------------------------------------------------
    def callback_head_a1(self, arg):
        self.crc_head_buf = [0xa1]
        self.last_bit = 1

    # --------------------------------------------------------------------
    def callback_head_data(self, arg):
        self.crc_head_buf += arg
        self.last_bit = arg[len(arg)-1] & 1

        cyls_msb = {0xfe: 0, 0xff: 256, 0xfc: 512, 0xfd: 768}
        self.cylinder = cyls_msb[arg[0]] + arg[1]
        self.head = arg[2] & 0b00000111
        self.sector_size = arg[2] & 0b01100000
        if arg[2] & 0b10000000:
            self.bad = True
        self.sector = arg[3]

    # --------------------------------------------------------------------
    def callback_data_a1(self, arg):
        self.crc_data_buf = [0xa1]
        self.last_bit = 1

    # --------------------------------------------------------------------
    def callback_data_marker(self, arg):
        self.crc_data_buf += arg
        self.last_bit = arg[len(arg)-1] & 1

    # --------------------------------------------------------------------
    def callback_data_data(self, arg):
        self.crc_data_buf += arg
        self.last_bit = arg[len(arg)-1] & 1
        self.data = arg

    # --------------------------------------------------------------------
    def callback_none(self, arg):
        pass

    # --------------------------------------------------------------------
    def feed(self, s):
        result = self.layout[self.phase].feed(s)

        # Still cooking, get next sample
        if result == State.COOKING:
            return

        # Phase is done, but we're still cooking
        elif result == State.DONE:
            self.phase += 1
            self.layout[self.phase].last(self.last_bit)
            return State.COOKING

        # Phase failed, cooking failed
        elif result == State.FAILED:
            print(" * Failed at: {}".format(self.layout[self.phase].name))
            self.phase = 0
            return State.FAILED

        # Last phase done, loop over and return success!
        elif result == State.LOOP_END:
            phase = 0
            return State.DONE

    # --------------------------------------------------------------------
    def __len__(self):
        return len(self.data)

    # --------------------------------------------------------------------
    def __bytes__(self):
        return bytes(self.data)


# --------------------------------------------------------------------
# Sector format for WD1006V-MM1 controller
class SectorWD(MFMSector):

    # --------------------------------------------------------------------
    def __init__(self):
        sector_size = 512
        super(SectorWD, self).__init__(sector_size)
        self.crc16_alg = crc_algorithms.Crc(width = 16, poly = 0x1021, reflect_in = False, xor_in = 0xffff, reflect_out = False, xor_out = 0x0000);
        self.crc32_alg = crc_algorithms.Crc(width = 32, poly = 0x140a0445, reflect_in = False, xor_in = 0xffffffff, reflect_out = False, xor_out = 0x0000);
        self.layout = [
            BitSeqFinder("Head SYNC", MFMSector.SYNC, 18*8*2, self.callback_none),
            BitSeqFinder("Head A1", MFMSector.A1, 3*8*2, self.callback_head_a1),
            ByteReader("Head data", 4, self.callback_head_data),
            ByteReader("Head CRC", 2, self.callback_head_crc),
            Skipper("Gap", 3*8*2),
            BitSeqFinder("Data Sync", MFMSector.SYNC, 3*8*2, self.callback_none),
            BitSeqFinder("Data A1", MFMSector.A1, 3*8*2, self.callback_data_a1),
            ByteReader("Data marker", 1, self.callback_data_marker),
            ByteReader("Data", sector_size, self.callback_data_data),
            ByteReader("Data CRC", 4, self.callback_data_crc),
            Skipper("Gap", 16*8*2),
            Looper()
        ]

   # --------------------------------------------------------------------
    def callback_head_crc(self, arg):
        crc_read = arg[0]*256 + arg[1]
        crc_computed = self.crc16_alg.bit_by_bit_fast(''.join([chr(x) for x in self.crc_head_buf]))
        if crc_read == crc_computed:
            self.head_crc_ok = True

    # --------------------------------------------------------------------
    def callback_data_crc(self, arg):
        crc_read = arg[0]*16777216 + arg[1]*65536 + arg[2]*256 + arg[3]
        crc_computed = self.crc32_alg.bit_by_bit_fast(''.join([chr(x) for x in self.crc_data_buf]))
        if crc_read == crc_computed:
            self.data_crc_ok = True


# --------------------------------------------------------------------
# Sector format for MERA-400 Intel C82062 based Amepol disk controller
class SectorAmepol(MFMSector):

    # --------------------------------------------------------------------
    def __init__(self):
        sector_size = 512
        super(SectorAmepol, self).__init__(sector_size)

        self.crc16_alg = crc_algorithms.Crc(width = 16, poly = 0x1021, reflect_in = False, xor_in = 0xffff, reflect_out = False, xor_out = 0x0000);

        self.layout = [
            BitSeqFinder("Head SYNC", MFMSector.SYNC, 750, self.callback_none),
            BitSeqFinder("Head A1", MFMSector.A1, 5*8*2, self.callback_head_a1),
            ByteReader("Head data", 4, self.callback_head_data),
            ByteReader("Head CRC", 2, self.callback_head_crc),
            Skipper("Gap", 60),
            BitSeqFinder("Data Sync", MFMSector.SYNC, 5*8*2, self.callback_none),
            BitSeqFinder("Data A1", MFMSector.A1, 3*8*2, self.callback_data_a1),
            ByteReader("Data marker", 1, self.callback_data_marker),
            ByteReader("Data", sector_size, self.callback_data_data),
            ByteReader("Data CRC", 2, self.callback_data_crc),
            Skipper("Gap", 16*8*2),
            Looper()
        ]

    # --------------------------------------------------------------------
    def callback_head_crc(self, arg):
        crc_read = arg[0]*256 + arg[1]
        crc_computed = self.crc16_alg.bit_by_bit_fast(''.join([chr(x) for x in self.crc_head_buf]))
        if crc_read == crc_computed:
            self.head_crc_ok = True

    # --------------------------------------------------------------------
    def callback_data_crc(self, arg):
        crc_read = arg[0]*256 + arg[1]
        crc_computed = self.crc16_alg.bit_by_bit_fast(''.join([chr(x) for x in self.crc_data_buf]))
        if crc_read == crc_computed:
            self.data_crc_ok = True


# --------------------------------------------------------------------
# Sector format for MERA-400 WD 2010-based Computex disk controller
class SectorComputex(MFMSector):

    # --------------------------------------------------------------------
    def __init__(self):
        sector_size = 512
        super(SectorComputex, self).__init__(sector_size)

        self.crc16_alg = crc_algorithms.Crc(width = 16, poly = 0x1021, reflect_in = False, xor_in = 0xffff, reflect_out = False, xor_out = 0x0000);
        self.crc32_alg = crc_algorithms.Crc(width = 32, poly = 0x140a0445, reflect_in = False, xor_in = 0xffffffff, reflect_out = False, xor_out = 0x0000);

        self.layout = [
            BitSeqFinder("Head SYNC", MFMSector.SYNC, 750, self.callback_none),
            BitSeqFinder("Head A1", MFMSector.A1, 5*8*2, self.callback_head_a1),
            ByteReader("Head data", 4, self.callback_head_data),
            ByteReader("Head CRC", 2, self.callback_head_crc),
            Skipper("Gap", 60),
            BitSeqFinder("Data Sync", MFMSector.SYNC, 5*8*2, self.callback_none),
            BitSeqFinder("Data A1", MFMSector.A1, 3*8*2, self.callback_data_a1),
            ByteReader("Data marker", 1, self.callback_data_marker),
            ByteReader("Data", sector_size, self.callback_data_data),
            ByteReader("Data CRC", 4, self.callback_data_crc),
            Skipper("Gap", 16*8*2),
            Looper()
        ]

    # --------------------------------------------------------------------
    def callback_head_crc(self, arg):
        crc_read = arg[0]*256 + arg[1]
        crc_computed = self.crc16_alg.bit_by_bit_fast(''.join([chr(x) for x in self.crc_head_buf]))
        if crc_read == crc_computed:
            self.head_crc_ok = True

    # --------------------------------------------------------------------
    def callback_data_crc(self, arg):
        crc_read = arg[0]*16777216 + arg[1]*65536 + arg[2]*256 + arg[3]
        crc_computed = self.crc32_alg.bit_by_bit_fast(''.join([chr(x) for x in self.crc_data_buf]))
        if crc_read == crc_computed:
            self.data_crc_ok = True
