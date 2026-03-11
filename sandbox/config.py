from dataclasses import dataclass


@dataclass
class Config:
    MAX_STACK_LIMIT = 65536  # 64KB
    MAX_MAX_PROCESSES_AND_OR_THREADS = 64
    MAX_MEMORY_LIMIT = 256000  # 256MB
    MAX_CPU_TIME_LIMIT = 10
    MAX_WALL_TIME_LIMIT = 20
    MAX_MAX_FILE_SIZE = 4096  # 4KB
