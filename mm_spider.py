import re
import urllib
import urllib2
import threading
import time
import Queue
import hashlib
#from BeautifulSoup import BeautifulSoup
import os
import sys
import zlib

url_queue=Queue.Queue(0)
url_set=set()
pic_set=set()
pic_url_set=set()
number=0
threading_lock0=threading.Lock()
threading_lock1=threading.Lock()
threading_lock2=threading.Lock()


class spider_thread(threading.Thread):
    def __init__(self,no,path,url,limit,proxy):
        threading.Thread.__init__(self)
        self.start_time=str(time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time())))
        self.no=no
        print "Thread%d starting..."%(self.no)
        if path=='pics':
            path=os.getcwd()+'\\'+'pics'
        if not os.path.exists(path):
            os.mkdir(path)
        self.path=path
        self.url=url
        self.limit=limit
        self.proxy=proxy
        
        if bool(self.proxy):
            
            proxy_handler = urllib2.ProxyHandler({"http" : 'http://127.0.0.1:8087'})
        else:
            proxy_handler = urllib2.ProxyHandler({})
        opener = urllib2.build_opener(proxy_handler)
        try:
            urllib2.install_opener(opener)
        except Exception, e:
            print(str(e))
        self.__stop=False
        
        
    def run(self):
        self.stop_thread()
        while not self.__stop:
            self.stop_thread()
            if not self.__stop:
                url=url_queue.get()
                print "Thread%d [%s] delete url:%s from queue,queue size is %d,"%(self.no,str(time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))),url,url_queue.qsize())
                self.done_url(url)
            
        self.end_time=str(time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time())))
        print "Thread%d ended"%(self.no)
        print "Thread%d run between [%s] and [%s]"%(self.no,self.start_time,self.end_time)

    def done_url(self,url):
        if self.is_pic(url):
            self.get_pics(url)
        else:
            self.get_urls(url)
            
    def get_pics(self,url):
        try:
            req=urllib2.Request(url)
            req.add_header('Accept-Encoding', 'gzip, deflate')
            resp=urllib2.urlopen(req)
            if( ("Content-Encoding" in resp.info()) and (resp.info()['Content-Encoding'] == "gzip")) :
                data = zlib.decompress(resp.read(), 16+zlib.MAX_WBITS)
            else:
                data = resp.read()
        except Exception, e:
            print(str(e))
            print "Network download pic failure,exit"
            sys.exit(0)
            
        threading_lock1.acquire()
        if hashlib.md5(data).hexdigest() not in pic_set:
            pic_set.add(hashlib.md5(data).hexdigest())
            global number
            if int(self.limit)<0:
                path=self.path+'\\'+str(number)+'.jpg'
                f = file(path,"wb")
                f.write(data) 
                f.close()
                print "Thread%d [%s] download pic:%s ,have downloaded:%d,"%(self.no,str(time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))),url,number+1)
            else:
                if int(number)>=int(self.limit):
                    self.__stop=True
                else:
                    path=self.path+'\\'+str(number)+'.jpg'
                    #print path
                    f = file(path,"wb")
                    try:
                        f.write(data) 
                    except:
                        f.write(data)
                    f.close()
                    print "Thread%d [%s] download pic:%s ,have downloaded:%d,"%(self.no,str(time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))),url,number+1)
            number=number+1
        threading_lock1.release()
            
        
        
            
    def get_urls(self,url):
        try:
            req=urllib2.Request(url)
            req.add_header('Accept-Encoding', 'gzip, deflate')
            resp=urllib2.urlopen(req)
            if( ("Content-Encoding" in resp.info()) and (resp.info()['Content-Encoding'] == "gzip")) :
                html = zlib.decompress(resp.read(), 16+zlib.MAX_WBITS)
            else:
                html = resp.read()
            #html=urllib2.urlopen(req).read()
            #html = zlib.decompress(html, 16+zlib.MAX_WBITS);
            #print('123')
            #print html
        except Exception, e:
            print(str(e))
            print "Network download page failure,exit"
            sys.exit(0)
        re_urls=re.findall('<a.*?href="(.*?)".*?>',html,re.I)
        for i in re_urls:
            #print i
            if i[0:2]=='mm':
                temp_url=str(self.url)+'/'+str(i)
                threading_lock0.acquire()
                if hashlib.md5(temp_url).hexdigest() not in url_set:
                    url_set.add(hashlib.md5(temp_url).hexdigest())
                    url_queue.put(temp_url)
                    print "Thread%d [%s] add page_url:%s,queue size is %d,"%(self.no,str(time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))),temp_url,url_queue.qsize())
                threading_lock0.release()
                
            if i[0:3]=='/mm':
                temp_url=str(self.url)+str(i)
                threading_lock0.acquire()
                if hashlib.md5(temp_url).hexdigest() not in url_set:
                    url_set.add(hashlib.md5(temp_url).hexdigest())
                    url_queue.put(temp_url)
                    print "Thread%d [%s] add page_url:%s,queue size is %d,"%(self.no,str(time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))),temp_url,url_queue.qsize())
                threading_lock0.release()
        
        re_pic=re.findall('<img.*?src="(.*?)".*?>',html,re.I)
        for j in re_pic:
            threading_lock2.acquire()
            if self.is_pic(j) and hashlib.md5(j).hexdigest() not in pic_url_set:
                pic_url_set.add(hashlib.md5(j).hexdigest())
                url_queue.put(j)
                print "Thread%d [%s] add pic_url:%s,queue size is %d,"%(self.no,str(time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))),temp_url,url_queue.qsize())
            threading_lock2.release()
        
        #soup=BeautifulSoup(html)
        #print soup
        #for item in soup.fetch('a'):
        #    print item['href']
        
    def is_pic(self,url):
        if url[-4:]=='.jpg':
            return True
        else:
            return False
    
    def stop_thread(self):
        if url_queue.empty():
            print "url_queue is empty,Thread%d is sleeping for 5 seconds"%self.no
            time.sleep(5)
        if url_queue.empty():
            self.__stop=True


def call_main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-u',dest="url",default="http://www.22mm.cc",help='the target url',metavar="url")
    parser.add_option('-n',dest="number",default=10,help='the number of the threads',metavar="number")
    parser.add_option('-o',dest="directory",default='pics',help='the directory of the pictures',metavar="directory") 
    parser.add_option('-l',dest="limit",default=-1,help='the limit of the pictures\' number',metavar="limit") 
    parser.add_option('-p',dest="proxy",default=False,help='Set goagent',metavar="False or True,default is False")
    
    (options,_)=parser.parse_args()
    #print options
    
    #init seed url
    url_queue.put(options.url)
    url_set.add(hashlib.md5(options.url).hexdigest())
    
    
    #call for test
    for i in range(int(options.number)):
        thread=spider_thread(i,options.directory,options.url,options.limit,options.proxy)
        thread.start()


if __name__=='__main__':
    try:
        call_main()
    except:
        print('Failure~')