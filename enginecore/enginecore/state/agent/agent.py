"""Interface for 3-rd party programs managed by the assets (e.g. ipmi_sim, snmpsimd)"""
import atexit


class Agent:
    """Abstract Agent Class """

    agent_num = 1

    def __init__(self):
        self._process = None

    def start_agent(self):
        """Logic for starting up the agent """
        raise NotImplementedError

    @property
    def pid(self):
        """Get agent process id"""
        return self._process.pid

    def stop_agent(self):
        """Logic for agent's termination """
        if not self._process.poll():
            self._process.kill()

    def register_process(self, process):
        """Set process instance
        Args:
            process(Popen): process to be managed
        """
        self._process = process
        atexit.register(self.stop_agent)
