from lib.dequedict import DequeDict
from lib.heapdict import HeapDict
from lib.ASC_IP import ASC_IP
import numpy as np


class ASC_IP_LECAR:

    class LeCaR_Entry:
        def __init__(self, o_block, freq=1, time=0,o_size=1):
            self.o_block = o_block
            self.freq = freq
            self.time = time
            self.evicted_time = None
            self.o_size=o_size
        def __lt__(self, other):
            if self.freq == other.freq:
                return self.o_block < other.o_block
            return self.freq < other.freq




    def __init__(self, cache_size, **kwargs):
        np.random.seed(123)
        self.time = 0
        #self.debug=[]
        self.cache_size = cache_size
        self.asc_ip_lru = ASC_IP(cache_size)
        self.lfu = HeapDict()

        self.history_size = cache_size

        self.asc_ip_lru_hist = DequeDict()
        self.lfu_hist = DequeDict()

        self.initial_weight = 0.5

        self.learning_rate = 0.45

        self.discount_rate = 0.005**(1 / self.cache_size)

        self.W = np.array([self.initial_weight, 1 - self.initial_weight],
                          dtype=np.float32) #[W_LRU,W_LFU]
        

        self.DEBUG_requests=0
        self.DEBUG_hit=0
        self.DEBUG_LFU=0
        self.DEBUG_ASC_IP_LRU=0


    def __contains__(self, o_block):
        return o_block in self.lfu


    def addToCache(self, o_block, freq,o_size):
        x = self.LeCaR_Entry(o_block, freq, self.time,o_size)
        y= self.asc_ip_lru.entry(o_block,o_size)
        
        self.lfu[o_block] = x
        self.asc_ip_lru.admit(y)

    def getLRU(self, dequeDict):
        return dequeDict.first()

    def getHeapMin(self):
        return self.lfu.min()

    def getChoice(self):
        return 0 if np.random.rand() < self.W[0] else 1

#---------------------以下是LeCaR功能、以上是---------------------

    def addToHistory(self, x, policy):#給定lru,lfu

        policy_history = None
        if policy == 0:
            policy_history = self.asc_ip_lru_hist#用來調整lecar
        else:
            policy_history = self.lfu_hist

        while(x.o_size>(self.history_size-policy_history.cached_count)):
            evicted = self.getLRU(policy_history)
            del policy_history[evicted.o_block]
        policy_history[x.o_block] = x




    def evict(self):
        asc_ip_lru=self.asc_ip_lru.cache.first()
        
        lfu = self.getHeapMin()

        evicted = asc_ip_lru
        policy = self.getChoice()


        if policy == 0:
            self.DEBUG_ASC_IP_LRU+=1

            evicted = self.lfu[asc_ip_lru.o_block]
            evicted.evicted_time = self.time#用來算reqgret的
            self.addToHistory(evicted, policy)#先判斷有沒有滿 才放入histroy

            #delete from cache
            self.asc_ip_lru.evict()
            del self.lfu[evicted.o_block]

        else:
            self.DEBUG_LFU+=1
            evicted = lfu
            evicted.evicted_time = self.time#
            self.addToHistory(evicted, policy)#先判斷有沒有滿 才放入histroy

            #delete from cache
            self.asc_ip_lru.only_evict(evicted.o_block)#不公平 不希望影響c值 所以不使用evict()
            del self.lfu[evicted.o_block]

        

        return evicted.o_block, policy


    def hit(self, o_block):
        x = self.lfu[o_block]
        o_size=x.o_size
        x.time = self.time

        # self.asc_ip_lru.requests(o_block,o_size)
        self.asc_ip_lru.cache[o_block].hit=True

        x.freq += 1
        self.lfu[o_block] = x


    # def adjustWeights(self, rewardLRU, rewardLFU):
    #     reward = np.array([rewardLRU, rewardLFU], dtype=np.float32)
    #     self.W = self.W * np.exp(self.learning_rate * reward)
    #     self.W = self.W / np.sum(self.W)

    #     if self.W[0] >= 0.99:
    #         self.W = np.array([0.99, 0.01], dtype=np.float32)
    #     elif self.W[1] >= 0.99:
    #         self.W = np.array([0.01, 0.99], dtype=np.float32)

    def adjustWeights(self,policy,reward): #W=[w_lru,w_lfu]
        if policy=="LRU":
            self.W[1]=self.W[1]*np.exp(self.learning_rate*reward)    
        elif policy=="LFU":
            self.W[0]=self.W[0]*np.exp(self.learning_rate*reward)
        
        self.W[0] = self.W[0] / (self.W[0]+self.W[1])
        self.W[1] = 1-self.W[0]

        if self.W[0] >= 0.99:
            self.W = np.array([0.99, 0.01], dtype=np.float32)
        elif self.W[1] >= 0.99:
            self.W = np.array([0.01, 0.99], dtype=np.float32)



    def miss(self, o_block,o_size):
        evicted = None
        freq = 1
        policy="None"
        reward=0
        if o_block in self.asc_ip_lru_hist:
            policy="LRU"
            entry = self.asc_ip_lru_hist[o_block]
            freq = entry.freq + 1
            del self.asc_ip_lru_hist[o_block]
            reward=-(self.discount_rate**(self.time - entry.evicted_time))#為什麼加負號
            
        elif o_block in self.lfu_hist:
            policy="LFU"
            entry = self.lfu_hist[o_block]
            freq = entry.freq + 1
            del self.lfu_hist[o_block]
            reward=-(self.discount_rate**(self.time - entry.evicted_time))#為什麼加負號

        #更新權重
        self.adjustWeights(policy,reward)
        
        while(o_size>self.cache_size-self.lfu.cached_count):
            evicted, policy = self.evict()

        self.addToCache(o_block, freq,o_size)

        return evicted


    def DEBUG(self):
        hit_rate=round(100*self.DEBUG_hit/self.DEBUG_requests,2)
        error=0
        if self.lfu.cached_count!=self.asc_ip_lru.cache.cached_count:
            error+=1
        message="req:  "+str(self.DEBUG_requests)\
        +"  hit_rate:  "+str(hit_rate)\
        +"  ASC_IP_LRU:  "+str(self.DEBUG_ASC_IP_LRU)\
        +"  LFU:  "+str(self.DEBUG_LFU)\
        +"  c:  "+str(self.asc_ip_lru.c)\
        +"  error:  "+str(error)\
        +"  policy:  "+str("ASC_IP_LECAR")

        return message




    def requests(self, o_block,o_size):
        miss = True
        evicted = None
        
        self.DEBUG_requests+=1
        self.time += 1

        if o_block in self:
            self.DEBUG_hit+=1
            miss = False
            self.hit(o_block)
        else:
            evicted = self.miss(o_block,o_size)

        if not self.DEBUG_requests%10000:
            print(self.DEBUG())
        #self.debug.append(self.lru.cached_count)
        