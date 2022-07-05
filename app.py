from asyncio import sleep
import sched
import numpy as np  
from multiprocessing import Process, Pipe, Value, Manager
from multiprocessing.connection import Listener
from multiprocessing.managers import BaseManager
import more_itertools
import os
import time
import timeit
from apscheduler.schedulers.blocking import BlockingScheduler

REQUIRED_RATE_IN_MS = 1

def send_new_vector(p_input):
  vector = np.random.default_rng().normal(size=(50,)) 
  p_input.send_bytes(vector.tobytes())
  time.sleep(0.01)

def send_in_bindwidth(p_input):
  # use wall time as opposed to cpu time to include IO wait time
  inner_timeit = timeit.Timer(lambda: send_new_vector(p_input))
  inner_time = inner_timeit.timeit(1)
  time_to_hold = REQUIRED_RATE_IN_MS - inner_time
  time.sleep(time_to_hold)
  
def process1():
  manager = BaseManager(address=('', 50000), authkey=b'abc')
  server = manager.get_server()
  server.serve_forever()

    outer_timeit = timeit.Timer(lambda: send_in_bindwidth(p_input))
    outer_time = outer_timeit.timeit(1)

    print("*** sending vector ***")
    print(f"send rate: {(outer_time * 1000)} hertz")
    print()
    print()
  # vectors_count = Value('d', 0)
  # scheduler = BlockingScheduler()
  # scheduler.add_job(send_new_vector, 'interval', [p_input, scheduler, vectors_count], seconds=1, id='new_vector_job')


def process2(p_output, p_input):
    all_vectors = np.empty([100, 50], dtype=np.float64)
    for i in range(5):
      start_time = time.time()
      vector_bytes = p_output.recv_bytes()
      end_time = time.time()

      response_time = (end_time - start_time) * 100
      
      vector = np.frombuffer(vector_bytes, dtype=np.float64)
      all_vectors[i] = vector

      print(f"*** recieving vector {i + 1} / {5} ***")
      print(f"response rate: {response_time * 1000} hertz")
          

if __name__ == '__main__':
    p_output, p_input = Pipe(duplex=False)
    p1 = Process(target=process1, args=(p_output, p_input),)
    p2 = Process(target=process2, args=(p_output, p_input),)
    p1.start()
    p2.start()
    p1.join()
    p2.join()