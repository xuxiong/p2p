#coding=utf-8
import random

class Group:
  members = []
  n = 0
  #加入直播组
  def join(self, peer):
    self.members.append(peer)
    peer.index = self.n
    self.n += 1
    peer.group = self
    peer.select_source()
  
  #返回直播组中可能作为转发节点的候选列表，按照直播质量（目前是丢包率）排序  
  def candidates(self, n=10):
    candidates = sorted([m for m in self.members if m.available()], key=lambda m:m.loss_rate())  
    return candidates[:n]

class Peer:
  max = 0
  '''
  buflen:缓冲区长度
  loss_in:接受数据的丢包率
  loss_out:发送数据的丢包率
  max_source:数据来源上限
  max_sink:转发上限
  sla:服务质量要求，当lossrate大于sla时，需要重新select_source
  '''
  def __init__(self, buflen=10, loss_in=.0, loss_out=.0, max_source=1, max_sink=1, sla=.0):
    self.loss_in = loss_in
    self.loss_out = loss_out
    self.buflen = buflen
    self.max_source = max_source
    self.max_sink = max_sink
    self.sources, self.sinks = [], []
    self.data = []
    self.group = None
    self.index = None
    self.sla = sla
    self.datafrom = {}	
  
  #挑选源节点  
  def select_source(self):
    if self.index == 0: return
    for source in self.sources:
      source.remove_sink(self)
    self.sources = []           
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
    if self != peer and peer not in self.sources:# and peer not in self.downstream(): #避免环路
      self.sources.append(peer)
      peer.add_sink(self)            
    return True
  '''允许环路情况下有死循环	
  #所有下游节点
  def downstream(self):
    if self.sinks == []:
      return []
    else:
      sinks = self.sinks[:]	  
      for sink in self.sinks:
        sinks += sink.downstream()	  
      return sinks
  '''  
  def remove_sink(self, peer):
    self.sinks.remove(peer)
    
  def remove_source(self, peer):
    self.sources.remove(peer)  
        
  def put(self, message):
    mfrom = message['from'][0]
    if mfrom in self.datafrom.keys():#记录从不同源节点获取的消息数
      self.datafrom[mfrom] += 1
    else:
      self.datafrom[mfrom] = 1	
    data = message['data']
    buf = self.data[-1*self.buflen:]
    if len(self.data)>0 and (data < min(buf) or data in buf):#不处理重复数据包
      return
    if Peer.max < data:
      Peer.max = data  
    r = self.probability()
    if r > self.loss_in:
      self.data.append(data)
      r = self.probability()
      if r > self.loss_out:
        for sink in self.sinks:
          message['from'].insert(0, self)
          if sink not in message['from']:#不是环路数据		  
            sink.put({'from':message['from'], 'data':data})
          #else:
          #  print message['from']		  
		  
  #丢包率，start为开始计算丢包率的下标，若为负数（-n）则计算最近n个包的丢包率        
  def loss_rate(self, start=0, end=None):
    if self.index == 0: return 0
    mx = 0	
    if end == None:	
      data = self.data[start:]
      mx = Peer.max	  
    else:
      data = self.data[start:end]
      mx = max(data)	  
    if len(data) > 0:
      return 1 - 1.0*len(data)/(mx - min(data) + 1)        
    else:
      return 1
  '''允许环路情况下有死循环
  def depth(self):
    if len(self.sources) == 0: 
      return 0
    else:
      d = []
      for source in self.sources:
        d.append(source.depth()+1)
      return min(d)
  '''    
  def probability(self):
    return random.random() 
    
  def available(self):
    return len(self.sinks) < self.max_sink and (self.index == 0 or len(self.data) > self.buflen)
  
class Peer1(Peer):
  #挑选源节点  
  def select_source(self):
    if self.index == 0: return
    candidates = []	
    for peer in self.group.candidates():#找出max_source个与已有源不重复的候选源
      if peer not in self.sources:	
        candidates.append(peer)		
      if len(candidates) >= self.max_source:
        break
    candidates += self.sources #将已有的源和候选源合并一起，再后续选择
    candidates = sorted(candidates, key = lambda m:m.loss_rate())[:self.max_source] #对候选进行排序后，选出topN个
    for source in self.sources:	#删除不在topN中的已有源
      if source not in candidates:
        Peer.remove_source(self, source)		
        source.remove_sink(self)
    for c in candidates: #候选节点如果尚不在已有源中，则加入
      if len(self.sources) < self.max_source:
        self.add_source(c)
      else:
        break	  
		
if __name__ == '__main__':
  p0 = Peer(max_sink=5)#源节点，允许有5个下游节点
  group = Group()
  group.join(p0)
  for i in xrange(2000):
    message = {'from':[p0], 'data':i}
    p0.put(message)
    if i % 5 == 0 and i < 200:#每发5个包，有新节点加入
      '''
      if i%2 == 0:#偶数包加入的新节点缺省只有一个源节点
        p = Peer(loss_in=.2)
      else:#奇数包加入的新节点可有2个源节点
        p = Peer(loss_in=.2, max_source=2)
      '''
      p = Peer(loss_in=.2, max_source=2, max_sink=2)	
      group.join(p)         
    if i == 500:
      for p in group.members: p.select_source()
	  
  for p in group.members:
    #print '%d: loss:%f source:[%s] sinks:[%s]\ndata:%s' % (p.index, p.loss_rate(), ','.join([str(s.index) for s in p.sources]), ','.join([str(s.index) for s in p.sinks]), ','.join([str(d) for d in p.data]))
    print '%d: loss:%f source:[%s] sinks:[%s]' % (p.index, p.loss_rate(start=499), ','.join([str(s.index) for s in p.sources]), ','.join([str(s.index) for s in p.sinks]))
  i = 0	
  lr = []
  for p in group.members:  
	if p.loss_rate(end=499) >= p.loss_rate(start=499): i += 1
	lr.append(p.loss_rate())
  print 'p.loss_rate(end=499) >= p.loss_rate(start=499):', i
  print 'lossrate: max:%f min:%f mean:%f' % (max(lr), min(lr), sum(lr)/len(lr))	
	