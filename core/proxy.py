# region(python_imports)

import logging
import os
import threading
from functools import partial, cache
from multiprocessing import Pool, Manager
from typing import NamedTuple, Any
from concurrent.futures import ThreadPoolExecutor
import queue

# endregion

# region(project_imports)

from core.config import Config
from core.util import Util
from ui.messagebox import messagebox

# endregion

# region(Tuples)

class Event(NamedTuple):
    name: str
    payload: Any

class AsyncCtrlParams(NamedTuple):
    lock: any
    signal: any
    counter: any
    total: int
    queue: any

    def stopped(self):
        with self.lock:
            return self.signal.value > 0

    def inc(self):
        with self.lock:
            self.counter.value += 1
            return self.counter.value

    def notify(self, job_desc, item):
        curr = self.inc()
        skip = 1
        if self.total > 10:
            skip = 1 if (self.total - curr) <= 5 else 5
        if curr%skip!=0: return

        progress = curr*(100/self.total)
        self.queue.put(("UPDATE_STATUSBAR", 
            ((job_desc + f"{curr}/{self.total} {item}"), progress, False)))

class AsyncCtrlResults(NamedTuple):
    total: int
    canceled: bool
    error: Exception
    event_args: any

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)
logwriter.setLevel(Config().logger_log_level)

# endregion

class AsyncProxy:

# region(class_methods)

    @cache
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self):
        # singleton class. initialized only once
        if hasattr(self, "_initialized"):
            return

        # bnuch of attributes used in controlling the async process
        self.manager = Manager()
        self.mp_stop = self.manager.Value('i', 0)
        self.mp_counter = self.manager.Value('i', 0)
        self.mp_lock = self.manager.Lock()
        self.mp_process_pool = None
        self.mp_total_job = 0
        self.event_register = {}
        self.event_queue = self.manager.Queue()
        self._timer = None
        self._host = None
        self._threadpool = ThreadPoolExecutor(max_workers=3)

        # will set the proxy in config for others to pickup
        # cfg = Config()
        # cfg._proxy = self

        # this is a singleton class. We will not initialize it again
        self._initialized = True

    def __getattr__(self, attr): 
        if attr == "_host":
            raise AttributeError(attr)

        internal_host = self.__dict__.get("_host")
        if internal_host is not None:
            return getattr(internal_host, attr)

        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{attr}'")

# endregion

# region(general_operation)

    # starts the monitor
    def start(self) -> None:
        self._timer = self.after(500, self.monitor_event_queue)

    # stops the monitor
    def stop(self) -> None:
        self._threadpool.shutdown(cancel_futures=True)
        if self._timer is not None:
            self._timer.cancel()

    # checks if an async process is running
    def running(self) -> bool:
        # return self.mp_total_job > 0
        return self.mp_process_pool is not None

    # a similar function to tkinter.after
    def after(self, delay_ms, callback, *args, **kwargs) -> threading.Timer:
        delay_sec = delay_ms / 1000.0  # tkinter.after uses milliseconds
        self._timer = threading.Timer(delay_sec, callback, args=args, kwargs=kwargs)
        self._timer.start()
        return self._timer

    def cancel_operation(self) -> None:
        if self.running():
            with self.mp_lock:
                self.mp_stop.value = 1

# endregion

# region(event_manageemnt)

    # register an event
    def register_event(self, event_name: str, callback_func: Any) -> None:
        self.event_register[event_name] = callback_func

    # unregister an event
    def unregister_event(self, event_name: str) -> None:
        if event_name in self.event_register:
            del self.event_register[event_name]

    # post an event
    def post_event(self, event_name: str, event_args: Any) -> None:
        self.event_queue.put((event_name, event_args))

    # monitors the event queue
    def monitor_event_queue(self) -> None:
        try:
            while True:
                event_data = self.event_queue.get_nowait()
                event_name = event_data[0]
                if event_name not in self.event_register: return
                self._threadpool.submit(self.event_register[event_name], event_data[1])

        except queue.Empty:
            pass

        except Exception as e:
            logwriter.error(f"Exception occured in monitor_event_queue")
            logwriter.error(str(e))

        finally:
            self.after(500, self.monitor_event_queue)

# endregion

# region(async_multiprocess)

    # clean up control variables
    def reset_async_session(self):
        if self.mp_process_pool is not None:
            self.mp_process_pool.terminate()
        self.mp_process_pool = None
        self.mp_total_job = 0
        self.mp_stop.value = 0
        self.mp_counter.value = 0
        self.enable_cancel(False)
        self.reset_statusbar()

    # exit a running async session after completon
    def exit_async_session(self, event) -> None:
        self.reset_async_session()
        self.reset_statusbar()
        self.unregister_event(event.name)

    # to be used by other modules
    def evaluate_async_outcome(self, event) -> bool:
        async_ctrl_res = event.payload
        messages = []
        if async_ctrl_res.canceled: messages.append(f"User cancelled operation.")
        if async_ctrl_res.error != None: messages.append(f"Exception occured: {str(async_ctrl_res.error)}")
        if len(messages) > 0: messagebox.showerror("Error", "\n".join(messages))
        return len(messages) <= 0

    # returns all necessary control variables as a NamedTuple
    def async_ctrl_params(self) -> AsyncCtrlParams:
        return AsyncCtrlParams(
            lock =      self.mp_lock,
            signal =    self.mp_stop,
            counter =   self.mp_counter, 
            total =     self.mp_total_job,
            queue =     self.event_queue,
        )

    # main function to execute asynchronus processes
    def exec_async(self, worker_func, static_args, jobs, event_name, event_func, event_args=None):
        self.reset_async_session()

        self.mp_total_job = len(jobs)
        if self.mp_total_job <= 0: return
        self.update_statusbar(f"Preparing to process {self.mp_total_job} jobs...", 0)

        async_ctrl = self.async_ctrl_params()

        if static_args is not None:
            partial_func = partial(worker_func, async_ctrl, *static_args)
        else:
            partial_func = partial(worker_func, async_ctrl)

        self.register_event(event_name, event_func)

        number_of_workers = min(4, max(1, os.cpu_count()))
        batch_size = -1* ( (-1 * self.mp_total_job) // (10 * number_of_workers))
        batches = Util.chunk_generator(jobs, batch_size)

        self.mp_process_pool = Pool(processes=number_of_workers)
        async_results = self.mp_process_pool.map_async(partial_func, batches)
        self.mp_process_pool.close()
        self.enable_cancel(True)

        self.monitor_async_session(async_results, event_name, event_args)

    # monitors the running async process
    def monitor_async_session(self, async_results, event_name, event_args):
        if not async_results.ready():
            return self.after(1000, self.monitor_async_session, 
                async_results, event_name, event_args)

        self.enable_cancel(False)
        self.reset_statusbar()

        total = self.mp_total_job
        canceled = False
        error = None
        results = []

        with self.mp_lock:
            canceled = self.mp_stop.value > 0

        try: 
            for r in async_results.get():
                pass
        except Exception as e:
            error = e

        self.reset_async_session()

        event = Event(name=event_name, payload= AsyncCtrlResults(total= total, 
            canceled= canceled, error= error, event_args= event_args))
        
        self.post_event(event_name, event)
        return 0

# endregion

