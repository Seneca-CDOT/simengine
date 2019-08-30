"""An iteration-handling utility that watches for incoming events
in a thread and launches an iteration"""

import queue
import threading


class EngineIterationConsumer:
    """This wrapper watches an event queue in a separate thread
    and launches a processing iteration (e.g. a chain of power events
    that occurred due to power outage)"""

    def __init__(self, iteration_worker_name="unspecified"):

        # queue of engine events waiting to be processed
        self._event_queue = queue.Queue()
        self._iteration_done_event = threading.Event()
        # work-in-progress
        self._current_iteration = None
        self._worker_thread = None
        self._on_iteration_launched = None
        self._iteration_worker_name = iteration_worker_name

    @property
    def current_iteration(self):
        """Iteration that is in progress/not yet completed
        (e.g. power downstream update still going on)"""
        return self._current_iteration

    def start(self, on_iteration_launched=None):
        """Launches consumer thread
        Args:
            on_iteration_launched(callable): called when event queue returns
                                             new iteration
        """
        self._on_iteration_launched = on_iteration_launched

        # initialize processing thread
        self._worker_thread = threading.Thread(
            target=self._worker, name=self._iteration_worker_name
        )
        self._worker_thread.daemon = True
        self._worker_thread.start()
        self._iteration_done_event.set()

    def stop(self):
        """Join consumer thread (stop processing power queued power iterations)"""
        if self._current_iteration:
            self._complete_task()
            self._event_queue.join()

        self.queue_iteration(None)
        self._iteration_done_event.set()
        self._worker_thread.join()

    def queue_iteration(self, iteration):
        """Queue an iteration for later processing;
        it will get dequeued once current_iteration is completed
        Args:
            iteration(EngineIteration): to be queued, event consumer will stop
                                        if None is supplied
        """
        self._event_queue.put(iteration)
        if not self._current_iteration:
            self._iteration_done_event.set()

    def unfreeze_task_queue(self):
        """Signal that current iteration is done (so handler can process
         next event in a queue if available)"""

        assert self.current_iteration.iteration_done
        self._complete_task()

    def _complete_task(self):
        """Resets current iteration and signals _worker to accept new queued tasks"""
        self._current_iteration = None
        self._event_queue.task_done()
        self._iteration_done_event.set()

    def _worker(self):
        """Consumer processing event queue, calls a callback supplied in
        start()"""

        while True:

            self._iteration_done_event.wait()

            # new processing iteration/loop was initialized
            next_iter = self._event_queue.get()

            if not next_iter:
                return

            assert self._current_iteration is None

            self._current_iteration = next_iter
            launch_results = self._current_iteration.launch()

            if self._on_iteration_launched:
                self._on_iteration_launched(*launch_results)

            self._iteration_done_event.clear()
