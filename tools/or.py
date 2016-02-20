import sys,os
import sys, os
sys.path.append('./tools/')
import traversal, bfutils
import graphkit as gk
import numpy as np
from numpy import ravel_multi_index as rmi
from ortools.constraint_solver import pywrapcp

U = 2
N = 10
k = 1

solver = pywrapcp.Solver("MSL")

# generate a random graph and undersample
g = bfutils.ringmore(N,k)
gdens = traversal.density(g)
g2 = bfutils.undersample(g,U-1)

# undersampled edges
dedgeu = {}
bedgeu = {}
for i in range(N):
    for j in range(N):
        dedgeu[(i,j)] = 0
        bedgeu[(i,j)] = 0
        v = str(i+1)
        w = str(j+1)
        if w in g2[v]:
            if (0,1) in g2[v][w]: dedgeu[(i,j)] = 1
            if (2,0) in g2[v][w]: bedgeu[(i,j)] = 1
        

# declare variables
edges = []
for i in range(N):
    e = []
    for j in range(N):
        e.append(solver.IntVar(0,1,"%i -> %i" % (i,j)))
    edges.append(e)

# directed path constraint
def apath(i,j,u, e=edges, s=solver):
    n = len(e)
    if u == 1: return [e[i][k]*e[k][j] for k in range(n)]
    l = []
    for k in range(n):
        for z in range(n):
            l.extend(map(lambda x: e[i][k]*x*e[z][j], apath(k,z,u-1)))
    return l                

def dcons(i, j, u, e=edges, s=solver):
    return s.Sum(apath(i,j,u,e=e,s=s))
#def bcons(i, j, u, e=edges, s=solver):
    
# declare constraints
for i in range(N):
    for j in range(N):
        # directed edge constraints
        de = dcons(i,j,U-1) 
        if dedgeu[(i,j)] == 1:
            solver.Add( 0 < de )
        else:
            solver.Add( 0 == de)

        # bidirected edge constraints
for i in range(N):
    for j in range(i,N):
        if j == i: continue        
        be = solver.Sum([edges[k][i]*edges[k][j] for k in range(N)])
        if bedgeu[(i,j)] == 1:
            solver.Add( 0 < be )
        else:
            solver.Add( 0 == be)


# run the solver
solution = solver.Assignment()
solution.Add([edges[i][j] for i in range(N) for j in range(N)])
collector = solver.AllSolutionCollector(solution)
solver.Solve(solver.Phase([edges[i][j] for i in range(N) for j in range(N)],
                          solver.CHOOSE_FIRST_UNBOUND,
                          solver.ASSIGN_MIN_VALUE),
                          [collector])
num_solutions = collector.SolutionCount()

# output solutions
print "num_solutions:", num_solutions
print "failures:", solver.Failures()
print "branches:", solver.Branches()
print "WallTime:", solver.WallTime()

if num_solutions > 0 and num_solutions < 5:
    for s in range(num_solutions):
        qval = [collector.Value(s, edges[i][j]) for i in range(N) for j in range(N)]
        for i in range(len(qval)):
            if qval[i]:
                e = np.unravel_index(i,[N,N])
                print e[0],"->",e[1]
        print
        print
