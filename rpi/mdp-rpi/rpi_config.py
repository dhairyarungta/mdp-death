RPI_IP = "192.168.14.1"
MSG_LOG_MAX_SIZE = 150 # characters

# PC Interface
PC_PORT = 8888
PC_BUFFER_SIZE = 2048

# Android Interface
BT_UUID = "00001101-0000-1000-8000-00805f9b34fb" 
BT_BUFFER_SIZE = 2048

# STM Interface
STM_BAUDRATE = 115200
STM_ACK_MSG = "A"
STM_COMMAND_FORMAT = '^[SLR][FB][0-9]{3}$'
STM_COMMAND_ADJUSTMENT_MAP = {
    # 90 degree turns
    "RF090": ["SF007", "RF090", "SB007"],
    "LF090": ["SF007", "LF090", "SB011"],
    "RB090": ["SF009", "RB090", "SB009"],
    "LB090": ["SF010", "LB090", "SB008"],
    # 180 degree turns
    "RF180": ["SF007", "RF180", "SB007"],
    "LF180": ["SF007", "LF090", "SB004", "LF090", "SB011"],
    "RB180": ["SF009", "RB180", "SB009"],
    "LB180": ["SF010", "LB090", "SF002", "LB090", "SB008"],
    # 270 degree turns
    "RF270": ["SF007", "RF2700", "SB007"],
    "LF270": ["SF007", "LF090", "SB004", "LF090", "SB004", "LF090", "SB011"],
    "RB270": ["SF009", "RB270", "SB009"],
    "LB270": ["SF010", "LB090", "SF002", "LB090", "SF002", "LB090", "SB008"]
}


# Image recognition