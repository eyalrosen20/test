import numpy as np  
import logging, time, timeit, os, socket, sys, socketserver
import datetime as dt
from multiprocessing import Process
from multiprocessing.managers import BaseManager
import multiprocessing as mp

REQUIRED_RATE_IN_MS = 1
HOST, PORT = "localhost", 4000
NUM_VECTORS = 100

def send_in_bindwidth(request):
  # use wall time as opposed to cpu time to include IO wait time
  start_time = dt.datetime.now()
  vector = np.random.default_rng().normal(size=(50,))
  elapsed = (dt.datetime.now() - start_time).microseconds / 10000
  time_to_hold = REQUIRED_RATE_IN_MS - elapsed 
  time.sleep(time_to_hold)
  request.send(vector.tobytes())
  elapsed = (dt.datetime.now() - start_time).microseconds / 10000
  print(f"sending rate: {round(elapsed * 10, 2)} hertz")

class MyTCPHandler(socketserver.BaseRequestHandler):
  def handle(self):
    self.data = self.request.recv(1024).strip()
    send_in_bindwidth(self.request)
    return
  
def process1():
  with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
    server.serve_forever()

def get_new_vector(sock):
  start_time = dt.datetime.now()
  sock.sendall(bytes("NEW_VECTOR\n", "utf-8"))
  vector_bytes = sock.recv(1024)
  vector = np.frombuffer(vector_bytes, dtype=np.float64)
  elapsed = (dt.datetime.now() - start_time).microseconds / 10000
  print(f"recieving rate: {round(elapsed * 10, 2)} hertz")
  return vector

def process2():
  time.sleep(2)

  all_vectors = np.empty([100, 50], dtype=np.float64)
  for i in range(NUM_VECTORS):
    print(f"*** recieving vector {i + 1} / {NUM_VECTORS} ***")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
      sock.connect((HOST, PORT))
      vector = get_new_vector(sock)
      all_vectors[i] = vector
    print()          

if __name__ == '__main__':
    p1 = Process(target=process1, args=(),)
    p2 = Process(target=process2, args=(),)
    p1.start()
    p2.start()
    p1.join()
    p2.join()