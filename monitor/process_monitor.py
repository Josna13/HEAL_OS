"""
HealOS 2.0 - Process Monitor
Inspects running operating system processes, tracks target application state,
and gracefully handles process-level permission errors and vanished processes.
Does NOT terminate or manipulate arbitrary system processes.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import psutil

from logger.healos_logger import get_system_logger, get_error_logger


@dataclass
class ProcessInfo:
    """Encapsulates lightweight information about a single system process."""
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float
    create_time: float
    cmdline: str
    memory_mb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "name": self.name,
            "status": self.status,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_mb": self.memory_mb,
            "create_time": self.create_time,
            "cmdline": self.cmdline,
        }


class ProcessMonitor:
    """
    Provides safe querying and tracking of operating system processes.
    """

    def __init__(self):
        self.logger = get_system_logger()

    @staticmethod
    def get_process_count() -> int:
        """Returns total count of running processes."""
        try:
            return len(psutil.pids())
        except Exception:
            return 0

    @staticmethod
    def is_pid_alive(pid: int) -> bool:
        """
        Verifies if a specific PID exists, is accessible, and is not a zombie.
        """
        if pid <= 0:
            return False
        try:
            p = psutil.Process(pid)
            if not p.is_running():
                return False
            status = p.status()
            return status != psutil.STATUS_ZOMBIE and status != psutil.STATUS_DEAD
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False
        except Exception:
            return False

    @staticmethod
    def get_process_details(pid: int) -> Optional[ProcessInfo]:
        """
        Retrieves detailed metadata for a given PID safely.
        """
        try:
            p = psutil.Process(pid)
            with p.oneshot():
                name = p.name()
                status = p.status()
                try:
                    cpu = p.cpu_percent(interval=None)
                except Exception:
                    cpu = 0.0
                try:
                    mem = p.memory_percent()
                except Exception:
                    mem = 0.0
                try:
                    mem_info = p.memory_info()
                    memory_mb = round(mem_info.rss / (1024 * 1024), 2)
                except Exception:
                    memory_mb = 0.0
                try:
                    create_time = p.create_time()
                except Exception:
                    create_time = 0.0
                try:
                    cmdline_list = p.cmdline()
                    cmdline = " ".join(cmdline_list)
                except Exception:
                    cmdline = ""

                return ProcessInfo(
                    pid=pid,
                    name=name,
                    status=status,
                    cpu_percent=round(cpu, 2),
                    memory_percent=round(mem, 2),
                    create_time=create_time,
                    cmdline=cmdline,
                    memory_mb=memory_mb,
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
        except Exception as e:
            get_error_logger().debug(f"Failed to fetch process info for PID {pid}: {e}")
            return None

    def find_processes_by_identifier(self, identifier: str) -> List[ProcessInfo]:
        """
        Finds all active processes whose name or command line contains the identifier.
        """
        matches: List[ProcessInfo] = []
        for proc in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
            try:
                name = proc.info.get("name") or ""
                cmdline_parts = proc.info.get("cmdline") or []
                cmdline = " ".join(cmdline_parts)

                if identifier in name or identifier in cmdline:
                    info = self.get_process_details(proc.pid)
                    if info:
                        matches.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue
        return matches

    def list_processes(self, limit: int = 50) -> List[ProcessInfo]:
        """
        Returns a sample of active system processes up to the specified limit.
        """
        results: List[ProcessInfo] = []
        for proc in psutil.process_iter(attrs=["pid"]):
            try:
                info = self.get_process_details(proc.pid)
                if info:
                    results.append(info)
                if len(results) >= limit:
                    break
            except Exception:
                continue
        return results
