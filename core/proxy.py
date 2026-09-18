# region(python_imports)

import logging
import os
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import cache, partial
from multiprocessing import Manager, Pool
from typing import Any, NamedTuple

# endregion

# region(project_imports)

from core.config import Config
from core.util import Util

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

        self._host = None
        self._started = False
        self.event_register = {}

        self._reset()

        # this is a singleton class. We will not initialize it again
        self._initialized = True

    def __getattr__(self, attr): 
        if attr == "_host":
            raise AttributeError(attr)

        internal_host = self.__dict__.get("_host")
        if internal_host is not None:
            return getattr(internal_host, attr)

        raise AttributeError(f"'{type(self).__name__}' host has no attribute '{attr}'")

# endregion

# region(general_operation)

    # starts the monitor
    def start(self) -> None:
        try:
            if self.started:
                return

            self.manager = Manager()
            self.mp_stop = self.manager.Value('i', 0)
            self.mp_counter = self.manager.Value('i', 0)
            self.mp_lock = self.manager.Lock()
            self.event_queue = self.manager.Queue()
            self._threadpool = ThreadPoolExecutor(max_workers=3)
            self.mp_process_pool = None
            self._started = True
            self._event_queue_monitor_timer = self._schedule_timer(500, self.monitor_event_queue)

        except Exception as e:
            self._reset()
            logwriter.debug(f"AsyncPrixy.start() - {str(e)}")
            raise e

    # stops the monitor
    def stop(self) -> None:
        try:
            if self.started:
                self._reset()

        except Exception as e:
            logwriter.debug(f"AsyncProxy.stop() - {str(e)}")

    # a similar function to tkinter.after
    def _schedule_timer(self, delay_ms, callback, *args, **kwargs) -> threading.Timer:
        if not self.started:
            return None

        delay_sec = delay_ms / 1000.0  # tkinter.after uses milliseconds
        timer = threading.Timer(delay_sec, callback, args=args, kwargs=kwargs)
        timer.start()

        return timer

    def cancel_operation(self) -> None:
        if self.started:
            if self.running:
                with self.mp_lock:
                    self.mp_stop.value = 1

# endregion

# region(properties)

    # checks if an async process is running
    @property
    def running(self) -> bool:
        return self.mp_process_pool is not None

    @property
    def started(self) -> bool:
        return self._started

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
        if self.started:
            self.event_queue.put((event_name, event_args))

    # monitors the event queue
    def monitor_event_queue(self) -> None:
        if not self.started:
            return

        try:
            while self.started:
                event_data = self.event_queue.get_nowait()
                event_name = event_data[0]
                if event_name not in self.event_register: return
                self._threadpool.submit(self.event_register[event_name], event_data[1])

        except queue.Empty:
            pass

        except Exception as e:
            logwriter.error(f"Exception occured in monitor_event_queue. {str(e)}")

        finally:
            self._event_queue_monitor_timer = self._schedule_timer(500, self.monitor_event_queue)

# endregion

# region(async_multiprocess)

    # exit a running async session after completon
    def exit_async_session(self, event) -> None:
        self._reset_ui()
        self._reset_async_session()
        if event is not None:
            self.unregister_event(event.name)

    # to be used by other modules
    def evaluate_async_outcome(self, event) -> bool:
        if not self.started:
            return

        async_ctrl_res = event.payload
        messages = []
        if async_ctrl_res.canceled: messages.append(f"Job aborted by user.")
        if async_ctrl_res.error != None: messages.append(f"Exception occured: {str(async_ctrl_res.error)}")
        if len(messages) > 0:
            self.showerror("Error", "\n".join(messages))
            logwriter.info('\n'.join(messages))
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
        if not self.started:
            return

        self.exit_async_session(event=None)

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

        if not self.started:
            return

        self.mp_process_pool = Pool(processes=number_of_workers)
        async_results = self.mp_process_pool.map_async(partial_func, batches)
        self.mp_process_pool.close()
        self.enable_cancel(True)

        self.monitor_async_session(async_results, event_name, event_args)

    # monitors the running async process
    def monitor_async_session(self, async_results, event_name, event_args) -> None:
        if not self.started:
            return

        if not async_results.ready():
            self._async_session_monitor_timer = self._schedule_timer(1000, self.monitor_async_session, 
                async_results, event_name, event_args)
            return

        self._reset_ui()

        total = self.mp_total_job
        with self.mp_lock:
            canceled = self.mp_stop.value > 0

        try: 
            error = None
            for r in async_results.get():
                pass
        except Exception as e:
            error = e

        self._reset_async_session()

        event = Event(name=event_name, payload= AsyncCtrlResults(total= total, 
            canceled= canceled, error= error, event_args= event_args))

        self.post_event(event_name, event)        

# endregion

# region(host_methods)

    def showinfo(self, title, message):
        if self._host is not None and hasattr(self._host, "showinfo"):
            self._host.showinfo(title=title, message=message)

    def showwarning(self, title, message):
        if self._host is not None and hasattr(self._host, "showwarning"):
            self._host.showwarning(title=title, message=message)

    def showerror(self, title, message):
        if self._host is not None and hasattr(self._host, "showerror"):
            self._host.showerror(title=title, message=message)

    def askyesno(self, title, message) -> bool:
        if self._host is not None and hasattr(self._host, "askyesno"):
            return self._host.askyesno(title=title, message=message)
        return False

    def enable_cancel(self, enable=True):
        if self._host is not None and hasattr(self._host, "enable_cancel"):
            self._host.enable_cancel(enable)

    def reset_statusbar(self):
        if self._host is not None and hasattr(self._host, "reset_statusbar"):
            self._host.reset_statusbar()

# endregion

# region(private_methods)

    # reset this class
    def _reset(self):
        self._started = False

        if hasattr(self, '_threadpool') and self._threadpool is not None:
            self._threadpool.shutdown(cancel_futures=True)
        self._threadpool = None

        if hasattr(self, '_event_queue_monitor_timer') and self._event_queue_monitor_timer is not None:
            self._event_queue_monitor_timer.cancel()
        self._event_queue_monitor_timer = None

        if hasattr(self, '_async_session_monitor_timer') and self._async_session_monitor_timer is not None:
            self._async_session_monitor_timer.cancel()
        self._async_session_monitor_timer = None

        # if hasattr(self, 'event_register') and self.event_register is not None:
        #     self.event_register.clear()
        # self.event_register = {}

        if hasattr(self, 'mp_process_pool') and self.mp_process_pool is not None:
            self.mp_process_pool.terminate()
            self.mp_process_pool.join()
        self.mp_process_pool = None

        if hasattr(self, 'event_queue') and self.event_queue is not None:
            try:
                while True:
                    self.event_queue.get_nowait()
            except queue.Empty:
                pass
        self.event_queue = None

        if hasattr(self, 'manager') and self.manager is not None:
            self.manager.shutdown()
        self.manager = None

        self.mp_stop = None
        self.mp_counter = None
        self.mp_lock = None
        self.mp_total_job = 0

    # clean up control variables
    def _reset_async_session(self):
        with self.mp_lock:
            self.mp_stop.value = 1

        if self.mp_process_pool is not None:
            self.mp_process_pool.join()
        self.mp_process_pool = None

        if self._async_session_monitor_timer is not None:
            self._async_session_monitor_timer.cancel()
        self._async_session_monitor_timer = None

        self.mp_total_job = 0

        with self.mp_lock:
            self.mp_stop.value = 0
            self.mp_counter.value = 0

    # reset Host UI to normal
    def _reset_ui(self):
        self.enable_cancel(False)
        self.reset_statusbar()

# endregion