
import numpy as np
from .dequedict import DequeDict



class ASC_IP():
    class entry:
        def __init__(self,o_block,o_size,admit=False,hit=False):
            self.o_block=o_block
            self.o_size=o_size
            self.admit=admit  # True=>MRU   ,False=>LRU
            self.hit=hit


    def __init__(self,cache_size,c=20000,delta=200):
        self.cache_size=cache_size
        self.c=c
        self.delta=delta

        self.cache=DequeDict()
        self.history=DequeDict()


    
    def addToHistory(self,obj):
        if not(obj.o_block in self.history):
            #清空間
            while(obj.o_size>self.cache_size-self.history.cached_count):
                self.history.popFirst()
        #放入
        self.history[obj.o_block]=obj

    
    def adjust_C(self,obj):
        if obj.admit==True:
            if obj.hit==False:
                self.c-=self.delta
        else:
            if obj.hit==False and (obj.o_block in self.history):
                self.c+=self.delta
        if self.c<=0:
            self.c=1



    def judge(self,obj):
        p=np.exp(-obj.o_size/self.c)
        r=np.random.rand()
        if obj.o_size>=self.c and p<=r:
            return False
        else:
            return True
        

    def only_evict(self,o_block): #lecar這類 當使用其他策略驅逐時 對C值估計會造成影響 故其他策略的驅逐不用來計算C值
        del self.cache[o_block]
        
    def evict(self):
        victim=self.cache.popFirst() #evict
        self.adjust_C(victim)
        self.addToHistory(victim)


    def admit(self,obj):
        if self.judge(obj):
            obj.admit=True
            obj.hit=False
            self.cache[obj.o_block]=obj#insert to MRU
        else:
            obj.admit=False
            obj.hit=False
            self.cache.pushFirst(obj.o_block,obj) #insert to LRU


    def requests(self,o_block,o_size):

        hit=o_block in self.cache
        curr_obj= self.cache[o_block] if hit else self.entry(o_block,o_size)
        
        if hit:
            curr_obj.hit=True
            self.cache[o_block]=curr_obj
        else:
            while(o_size>self.cache_size-self.cache.cached_count):
                self.evict()

            self.admit(curr_obj)
        
            

