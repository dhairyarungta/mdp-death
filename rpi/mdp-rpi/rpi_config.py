LOCATION = "IN" # IN (indoors) / OUT (outdoors)

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
STM_NAV_COMMAND_FORMAT = '^[SLR][FB][0-9]{3}$'
STM_GYRO_RESET_COMMAND = "GYROR"
STM_GYRO_RESET_DELAY = 8 # time to wait for gyro reset
STM_GYRO_RESET_FREQ = 14 # number of obstacles before GRYO RESET command is sent

# adjust commands for turns to correct turning radius to 30cm, as expected by PC-algo
STM_COMMAND_ADJUSTMENT_DICT = {
    "OUT": {
        # 90 degree turns: manually calibrated
        "RF090": ["SF007", "RF090", "SB008"],
        "LF090": ["SF007", "LF090", "SB011"],
        "RB090": ["SF009", "RB090", "SB009"],
        "LB090": ["SF009", "LB090", "SB006"],
        # 180 degree turns: manually calibrated
        "RF180": ["SF008", "RF180", "SB008"],
        "LF180": ["SF007", "LF090", "SB004", "LF090", "SB011"],
        "RB180": ["SF009", "RB180", "SB009"],
        "LB180": ["SF009", "LB090", "SF002", "LB090", "SB009"],
        # 270 degree turns: approximated using 180 degree turn + 90 degree turn
        "RF270": ["SF008", "RF270", "SB008"], 
        "LF270": ["SF007", "LF090", "SB004", "LF090", "SB004", "LF090", "SB011"],
        "RB270": ["SF009", "RB270", "SB009"],
        "LB270": ["SF009", "LB090", "SF002", "LB180", "SB006"]
    },
    "IN": {
        # 90 degree turns: manually calibrated
        "RF090": ["SF008", "RF090", "SB008"],
        "LF090": ["SF006", "LF090", "SB011"],
        "RB090": ["SF009", "RB090", "SB009"],
        "LB090": ["SF010", "LB090", "SB006"],
        # 180 degree turns: manually calibrated
        "RF180": ["SF006", "RF180", "SB012"],
        "LF180": ["SF006", "LF090", "SB005", "LF090", "SB012"],
        "RB180": ["SF009", "RB180", "SB008"],
        "LB180": ["SF009", "LB090", "SF003", "LB090", "SB007"],
        # 270 degree turns: approximated using 180 degree turn + 90 degree turn
        "RF270": ["SF006", "RF180", "SB004", "RF090", "SB008"], 
        "LF270": ["SF006", "LF090", "SB005", "LF090", "SB006", "LF090", "SB011"],
        "RB270": ["SF009", "RB270", "SB009"],
        "LB270": ["SF009", "LB090", "SF003", "LB090", "SF003", "LB090", "SB006"]
    },
}
STM_COMMAND_ADJUSTMENT_MAP = STM_COMMAND_ADJUSTMENT_DICT[LOCATION]

