from datetime import datetime, timedelta
import serial
import time


def bs2str(bs):
    return " ".join([f"{i:02X}" for i in bs])

class LD2450():
    CMD_HEADER = bytes([0xFD, 0xFC, 0xFB, 0xFA])
    CMD_EOF = bytes([0x04, 0x03, 0x02, 0x01])

    DATA_HEADER = bytes([0xAA, 0xFF, 0x03, 0x00])
    DATA_EOF = bytes([0x55, 0xCC])

    @staticmethod
    def _convert_data_int16(bs, signed):
        v = int.from_bytes(bs, byteorder='little')

        if signed:
            if v < 2**15:
                v = -v
            else:
                v = v - 2**15

        return v

    @staticmethod
    def _is_res_ok(res):
        flag = int.from_bytes(res[4:6], byteorder='little')
        return not flag

    def __init__(self, uartdev):
        try:
            self._ser = serial.Serial(uartdev, 256000, timeout=1)
        except:
            raise Exception(f"Failed to open UART device '{uartdev}'.") from None

    def __del__(self):
        try:
            self._ser.close()
        except:
            pass

    @property
    def in_waiting(self):
        return self._ser.in_waiting

    def _send_cmd(self, cmd_word, cmd_value, reverse_value=True): 
        cmd_word_str = bs2str(cmd_word)

        cmd_data_len = len(cmd_word + cmd_value)
        cmd_data_len = cmd_data_len.to_bytes(2, byteorder='little')

        cmd_word = bytes(cmd_word)[::-1]

        cmd_value = bytes(cmd_value)
        if reverse_value:
            cmd_value = cmd_value[::-1]

        cmd = self.CMD_HEADER + cmd_data_len + cmd_word + cmd_value + self.CMD_EOF
        self._ser.write(cmd)

        res = self._ser.read_until(self.CMD_EOF)

        #print(bs2str(cmd))
        #print(bs2str(res))
        #print()
        
        if self.CMD_HEADER in res:
            res = res.split(self.CMD_HEADER)[-1][:-4]
        else:
            raise Exception(f"No header in response to cmd '{cmd_word_str}'.")

        if not self._is_res_ok(res):
            raise Exception(f"No acknowledge in response to cmd '{cmd_word_str}'.")

        return res

    def _start_configuration(self):
        cmd_word = [0x00, 0xFF]
        cmd_value = [0x00, 0x01]
        self._send_cmd(cmd_word, cmd_value)

    def _end_configuration(self):
        cmd_word = [0x00, 0xFE]
        cmd_value = []
        self._send_cmd(cmd_word, cmd_value)

    def _execute_cmd(self, cmd_word, cmd_value, reverse_value=True):
        cmd_word_str = bs2str(cmd_word)

        n = 10
        for _ in range(n):
            try:
                self._start_configuration()
                break
            except:
                pass
        else:
            raise Exception("Failed to start configuration while executing cmd '{cmd_word_str}'.")

        for _ in range(n):
            try:
                res = self._send_cmd(cmd_word, cmd_value, reverse_value)
                break
            except:
                pass
        else:
            raise Exception("Failed to execute cmd '{cmd_word_str}'.")

        for _ in range(n):
            try:
                self._end_configuration()
                break
            except:
                pass
        else:
            raise Exception("Failed to end configuration while executing cmd '{cmd_word_str}'.")

        return res

    def get_firmware_version(self):
        cmd_word = [0x00, 0xA0]
        cmd_value = []
        res = self._execute_cmd(cmd_word, cmd_value)

        #ft = int.from_bytes(res[6:8], byteorder='little')
        vx = int.from_bytes(res[9:10], byteorder='little')
        vy = int.from_bytes(res[8:9], byteorder='little')
        vz = "".join([f"{i:02X}" for i in res[13:9:-1]])
        return f"V{vx}.{vy:02}.{vz}"

    def restart(self):
        cmd_word = [0x00, 0xA3]
        cmd_value = []
        self._execute_cmd(cmd_word, cmd_value)
        time.sleep(3)

    def restore_factory_settings(self, restart=False):
        # Baudrate: 256000.
        # Bluetooth: on.
        # Track mode: multi.
        # Area filtering: off.

        cmd_word = [0x00, 0xA2]
        cmd_value = []
        self._execute_cmd(cmd_word, cmd_value)

        if restart:
            self.restart()

    def set_baudrate(self, baudrate, restart=False):
        baudrates = [9600, 19200, 38400, 57600, 115200, 230400, 256000, 460800]
        if baudrate not in baudrates:
            baudrates_str = ", ".join(map(str, baudrates))
            raise ValueError(f"Baudrate must be one of the following: {baudrates_str}.")   

        baudrate_index = baudrates.index(baudrate) + 1

        cmd_word = [0x00, 0xA1]
        cmd_value = [0x00, baudrate_index]
        self._execute_cmd(cmd_word, cmd_value)

        if restart:
            self.restart()

    def get_mac_address(self):
        cmd_word = [0x00, 0xA5]
        cmd_value = [0x00, 0x01]
        res = self._execute_cmd(cmd_word, cmd_value)

        mac_address = bs2str(res[6:12])
        return mac_address

    def set_bluetooth_on(self, restart=False):
        cmd_word = [0x00, 0xA4]
        cmd_value = [0x00, 0x01]
        self._execute_cmd(cmd_word, cmd_value)

        if restart:
            self.restart()

    def set_bluetooth_off(self, restart=False):
        cmd_word = [0x00, 0xA4]
        cmd_value = [0x00, 0x00]
        self._execute_cmd(cmd_word, cmd_value)

        if restart:
            self.restart()

    def get_tracking_mode(self):
        # Tracking modes:
        # 1 - single target
        # 2 - multi target

        cmd_word = [0x00, 0x91]
        cmd_value = []
        res = self._execute_cmd(cmd_word, cmd_value)

        track_mode = int.from_bytes(res[6:8], byteorder='little')
        return track_mode

    def set_single_tracking(self):
        cmd_word = [0x00, 0x80]
        cmd_value = []
        self._execute_cmd(cmd_word, cmd_value)
    
    def set_multi_tracking(self):
        cmd_word = [0x00, 0x90]
        cmd_value = []
        self._execute_cmd(cmd_word, cmd_value)

    def get_zone_filtering(self):
        cmd_word = [0x00, 0xC1]
        cmd_value = []
        res = self._execute_cmd(cmd_word, cmd_value)
        #print(bs2str(res))

        # Zone filtering mode: 0 - off; 1 - in region; 2 - out of region.
        mode = int.from_bytes(res[6:8], byteorder='little')

        data = [mode]
        for i in range(3):
            from_i = (i+1) * 8
            to_i = from_i + 8
            c = res[from_i:to_i]

            x1 = int.from_bytes(c[0:2], byteorder='little', signed=True)
            y1 = int.from_bytes(c[2:4], byteorder='little', signed=True)
            x2 = int.from_bytes(c[4:6], byteorder='little', signed=True)
            y2 = int.from_bytes(c[6:8], byteorder='little', signed=True)
            data.extend([x1,y1,x2,y2])

        return data

    def set_zone_filtering(self, mode, reg1=None, reg2=None, reg3=None):
        cmd_word = [0x00, 0xC2]

        cmd_value = [mode, 0x00]
        for reg in [reg1,reg2,reg3]:
            if reg is None:
                regb = [0x00] * 8
            else:
                regb = []
                for i in reg:
                    ib = list(i.to_bytes(2, byteorder='little', signed=True))
                    regb.extend(ib)

            cmd_value.extend(regb)

        self._execute_cmd(cmd_word, cmd_value, reverse_value=False)

    def test(self):
        l1 = []
        l2 = []
        l3 = []
        
        for i in range(500):
            print(i)
        
            firmware_version = self.get_firmware_version()
            mac_address = self.get_mac_address()
            tracking_mode_index = self.get_tracking_mode()
        
            l1.append(firmware_version)
            l2.append(mac_address)
            l3.append(tracking_mode_index)
        
        print()
        for i in [l1, l2, l3]:
            print(sorted(set(i)))

    def get_all_data(self):
        return self._ser.read(size=self.in_waiting)

    def get_data(self):
        l = self._ser.read_until(self.DATA_EOF)

        #print(len(l), self.in_waiting)
        
        if l[-30:-26] != self.DATA_HEADER:
            print("Invalid data header")
            return
        
        l = l[-26:-4]

        data = []
        for i in range(3):
            from_i = i * 8
            to_i = from_i + 8
            c = l[from_i:to_i]

            x = self._convert_data_int16(c[0:2], signed=True)
            y = self._convert_data_int16(c[2:4], signed=True)
            data.extend([x,y])

            #s = self._convert_data_int16(c[4:6], signed=True)
            #d = self._convert_data_int16(c[4:6], signed=False)
            #data.extend([x,y,s,d])
        
        return data

if __name__ == "__main__":
    uartdev = "/dev/tty.usbserial-14410"
    r = LD2450(uartdev)

    r.set_bluetooth_on(restart=True)
    #r.set_bluetooth_off(restart=True)

    #r.set_single_tracking()
    r.set_multi_tracking()
        
    r.set_zone_filtering(mode=0)

    firmware_version = r.get_firmware_version()
    mac_address = r.get_mac_address()
    tracking_mode_index = r.get_tracking_mode()
    zone_filtering = r.get_zone_filtering()

    print(f"Firmware version: {firmware_version}")
    print(f"MAC address: {mac_address}")
    print(f"Tracking mode index: {tracking_mode_index}")
    print(f"Zone filtering: {zone_filtering}")

    input("\nPress Enter to start...\n")

    td = timedelta(seconds=1)

    dt_end = datetime.now() + td
    n = 0
    i = 0
    while True:
        data = r.get_data()
        if data is None:
            continue

        dt = datetime.now()
        if dt > dt_end:
            dt_end = dt + td
            n = i
            i = 0
            print()

        i += 1
        
        #x1,y1,s1,d1,x2,y2,s2,d2,x3,y3,s3,d3 = data
        #print(f"1) {x1:5}  {y1:5}  {s1:5}  {d1:5}")
        #print(f"2) {x2:5}  {y2:5}  {s2:5}  {d2:5}")
        #print(f"3) {x3:5}  {y3:5}  {s3:5}  {d3:5}")
        #print()

        x1,y1,x2,y2,x3,y3 = data
        print(f"{x1:5} {y1:5} | {x2:5} {y2:5} | {x3:5} {y3:5} | IN: {r.in_waiting:3} | samples/sec: {n:3}")

    # ====================

    #r.test()

    # ====================

    #for i in range(3):
    #    print('single')
    #    r.set_single_tracking()
    #    ind = r.get_tracking_mode()
    #    print(ind)
    #    time.sleep(5)
    #
    #    print('multi')
    #    r.set_multi_tracking()
    #    ind = r.get_tracking_mode()
    #    print(ind)
    #    time.sleep(5)

    # ====================

    #mode = 0
    #reg1 = None
    #
    #mode = 1
    #reg1 = None
    #
    #mode = 1
    #reg1 = [-3000, 3000, -1000, 4000]
    #
    #r.set_zone_filtering(mode, reg1)
    #v = r.get_zone_filtering()
    #print(v)

    # ====================
