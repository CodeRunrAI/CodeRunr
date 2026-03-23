from pydantic import BaseModel


# ---------------------------------------------------------------------------------------------
# All these parameters will be used at compilation time to check the program
# These can be over written by the client in API request


class SandboxConfig(BaseModel):
    # Max stack limit defined the maximum stack memory a program can use
    # Default limit is set to 64MB
    MAX_STACK_LIMIT: int = 65536

    # Max memory limit defined the maximum memory a program can use
    # If stack limit is not defined explicitly, then this memory will be counted in stack memory too.
    # Default limit is set to 256MB
    MAX_MEMORY_LIMIT: int = 262144

    # Max CPU time limit, If any program or process/thead takes more time than this
    # Program will be killed with no zero status code
    # Default is set to 30s
    MAX_CPU_TIME_LIMIT: float = 30

    # Max CPU wall time limit, this limit ensure program does not sleep more than this time
    # Any sleepy program will be killed with non zero status code if exceeded time limit
    # Default is set to 30
    MAX_WALL_TIME_LIMIT: float = 30

    # This limit restricts the file creation of size more than defined limit
    # If program tries to exceed this limit, will be killed
    # Default is set to 50MB
    MAX_MAX_FILE_SIZE: int = 51200

    # This limit will prevent any program or process to no create processes/thread
    # more than allowed limit
    # Default is set to 64
    MAX_MAX_PROCESSES_AND_OR_THREADS: int = 64
