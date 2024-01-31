import serial

class onr_ifslice():
    def __init__(self) -> None:
        self.connect()

    def connect(self, port):
        try:
            self.ser = serial.Serial(port, 115200, timeout=1)
        except IOError:
            print("Could not connect to the IF Slice")
        
    def set_attenuation(self, channel: int, attenuation: float):
            """
            Sets the attenuation level for a specific channel.

            Args:
                channel (int): The channel number.
                attenuation (float): The attenuation level to set.

            Returns:
                None
            """
            if self.ser.is_open:
                self.ser.write(f"ATTN {channel} {attenuation}".encode())
                self.ser.flush()
                response = self.ser.readline().decode()
                if response == "OK":
                    print("Attenuation set to ", attenuation)
            else:
                print("Serial port is not open")

    def get_attenuation(self):
        """
        Gets the attenuation level for all channels

        Returns:
            float[4]: The attenuation level for each channels
        """
        if self.ser.is_open:
            self.ser.write(f"ATTN?".encode())
            self.ser.flush()
            response = self.ser.readline().decode()
            response = response.split(",")
            return float(response)
        else:
            print("Serial port is not open")

    def close(self):
        """
        Closes the serial port.

        Returns:
            None
        """
        self.ser.close()
        print("Serial port closed")