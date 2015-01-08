import sys, os
sys.path.append('./tools/')
import traversal, bfutils
from multiprocessing import Pool,Process, Queue, cpu_count, current_process
import functools
import zickle as zkl
import time, socket
import scipy

INPNUM = 3 # number of randomized starts per graph
CAPSIZE= 1000 # stop traversing after growing equivalence class tothis size
REPEATS = 100
if socket.gethostname().split('.')[0] == 'leibnitz':
    PNUM=60
    PNUM=max((1,PNUM/INPNUM))
elif socket.gethostname().split('.')[0] == 'mars':
    PNUM=12
    PNUM=max((1,PNUM/INPNUM))
else:
    # Setting the number  of parallel running processes  to the number
    # of cores minus 7% for breathing room
    PNUM=cpu_count()-int(0.07*cpu_count())
    PNUM=max((1,PNUM/INPNUM))
print 'processes: ',PNUM, INPNUM

def wrapper(fold, n=10, k=10):
    scipy.random.seed()
    while True:
        try:
            g = bfutils.ringmore(n,k)
            g2 = traversal.increment_u(g,g)
            print fold,': ',traversal.density(g),':',
            startTime = int(round(time.time() * 1000))
            s = traversal.g22g1(g2, capsize=CAPSIZE)
            endTime = int(round(time.time() * 1000))
            print len(s)
        except MemoryError:
            print 'memory error... retrying'
            continue
        break
    return {'gt':g,'eq':s,'ms':endTime-startTime}

def killall(l):
    for e in l: 
        e.join(timeout=0.001)
        if not e.is_alive():
            #print 'first result'            
            for p in l:
                if p != e:
                    #print 'terminating ', p.name
                    p.terminate()
                    p.join()
                else:
                    p.join()
            return True
    return False

def fan_wrapper(fold,n=10,k=10):
    scipy.random.seed()
    curr_proc=current_process()
    curr_proc.daemon=False
    output = Queue()
    while True:
        try:
            g = bfutils.ringmore(n,k)
            gdens = traversal.density(g)
            g2 = traversal.increment_u(g,g)
            #g2 = bfutils.undersample(g,1)
            def inside_wrapper():
                scipy.random.seed()
                startTime = int(round(time.time() * 1000))
                s = traversal.v2g22g1(g2, capsize=CAPSIZE)
                endTime = int(round(time.time() * 1000))
                print "{:2}: {:8} : {:4}  {:10} seconds".format(fold, round(gdens,3), len(s), round((endTime-startTime)/1000.,3))
                output.put({'gt':g,'eq':s,'ms':endTime-startTime})
            pl = [Process(target=inside_wrapper) for x in range(INPNUM)]
            for e in pl: e.start()
            while True:
                if killall(pl): break
            r = output.get()           
        except MemoryError:
            print 'memory error... retrying'
            for p in pl:
		p.terminate()
		p.join()
            continue
        break
    for p in pl: p.join()
    return r

densities = {6: [0.2, 0.25, 0.3, 0.4, 0.5, 0.6],
             8: [0.15, 0.2, 0.25, 0.3],
             10:[0.1, 0.15, 0.2, 0.25, 0.3],
             15:[0.1, 0.15, 0.2, 0.25, 0.3],
             20:[0.2],#2, 0.25, 0.3],
             30:[0.1],
             40:[0.1],
             50:[0.05, 0.1],
             60:[0.05, 0.1]}

for nodes in [30]:
    z = {}
    pool=Pool(processes=PNUM)
    for dens in densities[nodes]:
        print "{:2}: {:8} : {:10}  {:10}".format('id', 'density', 'eq class', 'time')    
        e = bfutils.dens2edgenum(dens, n=nodes)
        eqclasses = pool.map(functools.partial(fan_wrapper, n=nodes, k=e), 
                             range(REPEATS))
        z[dens] = eqclasses
        zkl.save(z[dens],
                 socket.gethostname().split('.')[0]+\
                     '_nodes_'+str(nodes)+'_density_'+str(dens)+'_U333.zkl')
        print ''
        print '----'
        print ''
    pool.close()
    pool.join()
    zkl.save(z,socket.gethostname().split('.')[0]+'_nodes_'+str(nodes)+'_U333.zkl')
