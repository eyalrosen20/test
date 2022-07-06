import numpy as np  
import time
import sys
import socket, socketserver
import json
import datetime as dt
from multiprocessing import Process
import random
from threading import Thread

HOST, PORT = "localhost", 4000
VECTOR_SIZE = 50
JSON_FILENAME = "results.json"
SAVE_FREQUENCY = 1000

class AppConfig:
  use_noisy = False

def send_in_bindwidth(request):
  # use wall time as opposed to cpu time to include IO wait time
  start_time = dt.datetime.now()

  # if timer decided it's time to send a noisy response...
  if AppConfig.use_noisy == True:    
    # ... then send an empty numpy array
    print(f"\n*** sending noisy response ***\n")
    vector = np.empty([])

    # ... and continue sending random arrays from now on
    AppConfig.use_noisy = False
  else:
    vector = np.random.default_rng().normal(size=(VECTOR_SIZE,))

  request.send(vector.tobytes())
  micro_elapsed = (dt.datetime.now() - start_time).microseconds
  micro_to_hold = 1000 - micro_elapsed
  seconds_to_hold = abs(micro_to_hold / 1000000)
  time.sleep(seconds_to_hold)
  hertz = (dt.datetime.now() - start_time).microseconds
  print(f"sending rate: {hertz} hertz")


class MyTCPHandler(socketserver.BaseRequestHandler):
  def handle(self):
    self.data = self.request.recv(1024).strip()
    send_in_bindwidth(self.request)

def choose_if_noisy():
  while True:
    seconds = random.choice([2,3])
    print(f"\nwaiting {seconds} seconds before sending a noisy response...\n")
    time.sleep(seconds)
    AppConfig.use_noisy = True

def process1(flag):
  if flag == 'allow_noisy':
    Thread(target=choose_if_noisy, args=()).start()
  else:
    print("** not using noisy signals **")
  
  with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
    server.serve_forever()

def get_new_vector(sock):
  start_time = dt.datetime.now()
  sock.sendall(bytes("NEW_VECTOR\n", "utf-8"))
  vector_bytes = sock.recv(1024)
  vector = np.frombuffer(vector_bytes, dtype=np.float64)
  hertz = (dt.datetime.now() - start_time).microseconds * 10
  print(f"recieving rate: {hertz} hertz")
  return vector, hertz

def save_data_to_file(report):
  print(f"\n*** saving data to {JSON_FILENAME} ***")
  all_hertz = [x['acquisition_rate'] for x in report['vectors']]
  report['acquisition_rates'] = { 'mean': np.mean(all_hertz), 'std': np.std(all_hertz) }

  with open(JSON_FILENAME, 'w', encoding='utf-8') as file:
    json.dump(report, file, ensure_ascii=False, indent=4)

def process2():
  report = { 'vectors': [] }
  i = 0
  while True:
    print(f"*** recieving vector {i + 1} ***")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
      sock.connect((HOST, PORT))
      vector, hertz = get_new_vector(sock)
      if vector.size == 1:
        print(" ** DETECTED NOISY RESPONSE - IGNORING **")
        continue
      mean = np.mean(vector)
      std = np.std(vector)
      vector_report = { 'mean': mean, 'std': std, 'acquisition_rate': hertz }
      report['vectors'].append(vector_report)
    if i % SAVE_FREQUENCY == 0:
      save_data_to_file(report)
    i += 1
    print()

if __name__ == '__main__':
    flag = 'allow_noisy' if sys.argv.count('allow_noisy=true') == 1 else None
    p1 = Process(target=process1, args=(flag,))
    p2 = Process(target=process2, args=(),)
    p1.start()
    p2.start()
    p1.join()
    p2.join()