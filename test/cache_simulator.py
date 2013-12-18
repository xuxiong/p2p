#!/usr/bin/env python

import random

total = input('total:')
datasize = input('datasize:')
cachesize = input('cachesize:')
pecent1 = input('pecent1(top data pecentage):')
pecent2 = input('pecent2(top data occurrence pecentage):')

cache = []

i = int(datasize * pecent1)
top = range(i) * int(total * pecent2 / i)
rest = range(i, datasize) * int(total * (1 - pecent2) / (datasize - i))
series = top + rest
random.shuffle(series)
print len(series),len(top),len(rest)

hit, miss  = 0, 0
for d in series:
  if d in cache:
    hit += 1
    cache.remove(d)
    cache.append(d)
  else:
    miss += 1
    if len(cache) < cachesize : cache.append(d)
    else : cache[0] = d

print 'hit rate:%s' % (hit * 1.0/ len(series))
