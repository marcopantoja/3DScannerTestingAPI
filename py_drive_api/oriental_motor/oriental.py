"""
For holding certain constants related to the oriental motor devices
"""

class DriverModbusIO:
    """
    These are the signals assigned to the various bit positions in register
    0x007C --> 0x007F
    """
    # INPUTS:
    # Upper 0x007C


    # Lower 0x007D
    # SIGNAL    BIT Value
    M0      =   0b1                 # R-IN0
    M1      =   0b10                # R-IN1
    M2      =   0b100               # R-IN2
    START   =   0b1000              # R-IN3
    ZHOME   =   0b10000             # R-IN4
    STOP    =   0b100000            # R-IN5
    FREE    =   0b1000000           # R-IN6
    ALM_RST =   0b10000000          # R-IN7
    D_SEL0  =   0b100000000         # R-IN8
    D_SEL1  =   0b1000000000        # R-IN9
    D_SEL2  =   0b10000000000       # R-IN10
    SSTART  =   0b100000000000      # R-IN11
    FW_JOG_P=   0b1000000000000     # R-IN12
    RV_JOG_P=   0b10000000000000    # R-IN13
    FW_POS  =   0b100000000000000   # R-IN14
    RV_POS  =   0b1000000000000000  # R-IN15

    M0_OFF        =   0
    M1_OFF        =   0
    M2_OFF        =   0
    START_OFF     =   0
    ZHOME_OFF     =   0
    STOP_OFF      =   0
    FREE_OFF      =   0
    ALM_RST_OFF   =   0
    D_SEL0_OFF    =   0
    D_SEL1_OFF    =   0
    D_SEL2_OFF    =   0
    SSTART_OFF    =   0
    FW_JOG_P_OFF  =   0
    RV_JOG_P_OFF  =   0
    FW_POS_OFF    =   0
    RV_POS_OFF    =   0


    # OUTPUTS:
    # Upper 0x007E


    # Lower 0x007F
    # SIGNAL    BIT Value   
    M0_R     =  0b1                 # R-OUT0
    M1_R     =  0b10                # R-OUT1
    M2_R     =  0b100               # R-OUT2
    START_R  =  0b1000              # R-OUT3
    HOME_END =  0b10000             # R-OUT4
    READY    =  0b100000            # R-OUT5
    INFO     =  0b1000000           # R-OUT6
    ALM_A    =  0b10000000          # R-OUT7
    SYS_BSY  =  0b100000000         # R-OUT8
    AREA0    =  0b1000000000        # R-OUT9
    AREA1    =  0b10000000000       # R-OUT10
    AREA2    =  0b100000000000      # R-OUT11
    TIM      =  0b1000000000000     # R-OUT12
    MOVE     =  0b10000000000000    # R-OUT13
    IN_POS   =  0b100000000000000   # R-OUT14
    TLC      =  0b1000000000000000  # R-OUT15

    M0_R_OFF     =   0
    M1_R_OFF     =   0
    M2_R_OFF     =   0
    START_R_OFF  =   0
    HOME_END_OFF =   0
    READY_OFF    =   0
    INFO_OFF     =   0
    ALM_A_OFF    =   0
    SYS_BSY_OFF  =   0
    AREA0_OFF    =   0
    AREA1_OFF    =   0
    AREA2_OFF    =   0
    TIM_OFF      =   0
    MOVE_OFF     =   0
    IN_POS_OFF   =   0
    TLC_OFF      =   0