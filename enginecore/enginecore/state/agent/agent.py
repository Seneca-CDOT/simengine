"""Interface for 3-rd party programs managed by the assets (e.g. ipmi_sim, snmpsimd)"""
import atexit
import os


class Agent:
    """Abstract Agent Class """

    agent_num = 1

    def __init__(self):
        self._process = None
        Agent.agent_num += 1

    @property
    def pid(self):
        """Get agent process id"""
        return self._process.pid

    def process_running(self):
        """Returns true if process is running"""
        return os.path.exists("/proc/" + str(self.pid))

    def stop_agent(self):
        """Logic for agent's termination """
        if not self._process.poll():
            self._process.terminate()
            # Clean up the process table to prevent defunct
            self._process.wait()

    def start_agent(self):
        """Logic for starting up the agent """
        raise NotImplementedError

    def register_process(self, process):
        """Set process instance
        Args:
            process(Popen): process to be managed
        """
        self._process = process
        atexit.register(self.stop_agent)

    def __str__(self):
        agent_msg = "is {}running".format("" if self.process_running() else "not ")
        return "Agent #{0.agent_num}: {0.pid} ".format(self) + agent_msg
