
import numpy as np
from lib.ASC_IP import ASC_IP


'''
設計:
    1.可被其他演算法引用，做成lru 輸入cache_size 即可用req_seq序列操作

'''
class ASC_IP_LRU(ASC_IP):

    def __init__(self,cache_size,c=20000,delta=200):
        super().__init__(cache_size,c,delta)
        self.DEBUG_requests=0
        self.DEBUG_hitCount=0
        self.DEBUG_not_admit=0


    

    def admit(self,obj):
        super().admit(obj)
        if not self.judge(obj):
            self.DEBUG_not_admit+=1

    def requests(self,o_block,o_size):
        self.DEBUG_requests+=1
        if o_block in self.cache:
            self.DEBUG_hitCount+=1

        super().requests(o_block,o_size)
        


        if not self.DEBUG_requests%10000:
            message=""
            message+=self.DEBUG()
            print(message)

    def DEBUG(self):
        miss=self.DEBUG_requests-self.DEBUG_hitCount
        admit=miss-self.DEBUG_not_admit
        hit_rate=round(100*self.DEBUG_hitCount/self.DEBUG_requests,2)
        
        message="req: "+str(self.DEBUG_requests)\
        +"  hit: "+str(self.DEBUG_hitCount)\
        +"  hit_rate: "+str(hit_rate)\
        +"  c: "+str(self.c)\
        +"  admit: "+str(admit)\
        +"  not_admit: "+str(self.DEBUG_not_admit)\
        +"  cache_count: "+str(self.cache.cached_count)\
        +"  history: "+str(self.history.cached_count)\
        +"  policy: "+str("ASC_IP_LRU")

        return message

            

