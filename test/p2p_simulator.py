#coding=utf-8
import random

class Group:
  members = []
  n = 0
  
  def join(self, peer):
    self.members.append(peer)
    peer.index = self.n
    self.n += 1
    peer.group = self
    peer.run()
    
  def candidates(self, n=10):
    candidates = sorted([m for m in self.members if m.available()], key=lambda m:m.loss_rate())  
    return candidates[:n]

class Peer:
  max = 0
  
  def __init__(self, buflen=10, loss_in=.0, loss_out=.0, max_source=1, max_sink=1):
    self.loss_in = loss_in
    self.loss_out = loss_out
    self.buflen = buflen
    self.max_source = max_source
    self.max_sink = max_sink
    self.sources, self.sinks = [], []
    self.data = []
    self.group = None
    self.index = None
    
  def run(self):
    for peer in self.group.candidates():
      self.add_source(peer)
      if len(self.sources)>=self.max_source:
        break
        
  def add_sink(self, peer):
    if len(self.sinks)>=self.max_sink:
      return False
    if self != peer and peer not in self.sinks:
      self.sinks.append(peer)
    return True
      
  def add_source(self, peer):
    if len(self.sources)>=self.max_source:
      return False 
    if self != peer and peer not in self.sources: 
      self.sources.append(peer)
      peer.add_sink(self)            
    return True
      
  def remove_sink(self, peer):
    self.sinks.remove(peer)
    
  def remove_source(self, peer):
    self.sources.remove(peer)  
        
  def put(self, data):
    buf = self.data[-1*self.buflen:]
    if len(self.data)>0 and (data < min(buf) or data in buf):
      return
    if Peer.max < data:
      Peer.max = data  
    r = self.probability()
    if r > self.loss_in:
      self.data.append(data)
      r = self.probability()
      if r > self.loss_out:
        for sink in self.sinks:
          sink.put(data)
          
  def loss_rate(self, start=0):
    data = self.data[start:]
    if len(data) > 0:
      #print len(data), Peer.max, max(data), min(data), data
      return 1 - 1.0*len(data)/(max(data) - min(data) + 1)        
    else:
      return 1  
  
  def depth(self):
    if len(self.sources) == 0: 
      return 0
    else:
      d = []
      for source in self.sources:
        d.append(source.depth()+1)
      return min(d)
      
  def probability(self):
    return random.random() 
    
  def available(self):
    return len(self.sinks) < self.max_sink     
                
if __name__ == '__main__':
  p0 = Peer(max_sink=5)
  group = Group()
  group.join(p0)
  for i in xrange(100):
    p0.put(i)
    if i % 5 == 0:
      if i%2 == 0:
        p = Peer(loss_in=.2)
      else:
        p = Peer(loss_in=.2, max_source=2)
      group.join(p)         
  
  for p in group.members:
    print p.index, p.loss_rate(), ','.join([str(s.index) for s in p.sources])