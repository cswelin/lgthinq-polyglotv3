class Utilities:
    NotRunningStates = [
        "COOLDOWN", 
        "POWEROFF", 
        "POWERFAIL", 
        "INITIAL", 
        "PAUSE", 
        "AUDIBLE_DIAGNOSIS", 
        "FIRMWARE",
        "COURSE_DOWNLOAD", 
        "ERROR", 
        "END"
    ]

    state_to_gv = {
        "POWEROFF": 0,
        "RUNNING": 1,
        "DRYING": 1,
        "PAUSE": 2,
        "COOLDOWN": 3,
        "INITIAL": 4,
        "STANDBY": 5,
        "END": 20,
        "ERROR": 30
    }