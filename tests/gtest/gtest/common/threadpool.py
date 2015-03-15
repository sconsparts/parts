import threading
import traceback
import multiprocessing
import Queue
import sys

class Worker(threading.Thread):
    """Thread executing tasks from a given tasks queue"""
    printExcLock = threading.Lock()
    def __init__(self, tasks):
        threading.Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()
    
    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except:
                with self.printExcLock:
                    print >> sys.stderr, traceback.format_exc()
                    sys.stderr.flush()
            self.tasks.task_done()

class ThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, numThreads=multiprocessing.cpu_count()//2):
        self.tasks = Queue.Queue(numThreads)
        for t in range(numThreads):
            Worker(self.tasks)

    def addTask(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def waitCompletion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()

