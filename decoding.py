import numpy as np

def forward_backward(lls, tr, ip, fs, evaluate_only=False):
    """
    Not tested!!!
    """
    ltr = np.log(tr)
    lf = np.empty_like(lls); lf[:] = -np.inf
    lb = np.empty_like(lls); lb[:] = -np.inf
    lf[0] = lls[0] + np.log(ip)
    lb[fs,-1] = 0.0
    
    for ii in  xrange(1,len(lls)):
        lf[ii] =  lls[ii] + logsumexp(lf[ii-1] + ltr.T, axis=1)
    tll = logsumexp(lf[fs,-1])
    if evaluate_only:
      return tll
    for ii in reversed(xrange(len(lls)-1)):
        lb[ii] = logsumexp(ltr + lls[ii+1] + lb[ii+1], axis=1)
    sp = np.exp(lf + lb - tll)
    return tll, sp, lf, lb

def viterbi(lls, tr, ip, fs):
    ltr = np.log(tr)
    bt = np.zeros_like(lls, dtype=int)
    lf = lls[0] + np.log(ip)    
    for ii in  xrange(1,len(lls)):
        hypothesis = lf + ltr.T
        bt[ii] = np.argmax(hypothesis, axis=1)
        lf = lls[ii] + hypothesis[xrange(len(tr)),bt[ii]]
    path = [fs[np.argmax(lf[fs])]]
    for ii in  reversed(xrange(1,len(lls))):
      path.insert(0, bt[ii,path[0]])
    return path

def nstate_monophn_rec(lls, phns, penalty, sil_index=0):
  """
  Simple monophone loop decoder.
  Inputs:
    lls - matrix of pre-calculated log output probabilities, rows
          corresponds to frames and columns to HMM states. It is assumed
          that each phoneme is modeled by N-state left-to-right HMM.
          Therefore, lls matrix has len(phns)xN columns corresponding to:
          phn1-state1, phn1-state2, ..., phn1-stateN, phn2-state1, ...
    phns - list with phoneme names (ordered as in lls columns)
    penalty - phone insertion penalty
    sil_index - phns[sil_index] will always be the first and the last phoneme
          in the decoded sequence
  Output:
    list of phoneme names corresponding to the decoded sequence
    
  """
  # rearange lls to have all 1st states for all phonemes, then all 2nd states for all phonemes, ...
  lls = lls.reshape(lls.shape[0], len(phns), -1).transpose(0,2,1).reshape(*lls.shape)
  lf = np.empty(lls.shape[1])
  bt = np.zeros(lls.shape, dtype=int) + np.arange(lls.shape[1])
  penalty += np.log(1./len(phns))
  lf[:]=-np.inf
  lf[sil_index]=lls[0,sil_index]
  for ii in  xrange(1,len(lls)):
    lpi = np.argmax(lf[-len(phns):])+len(lf)-len(phns)
    lpv = lf[lpi]
    m = lf[len(phns):] < lf[:-len(phns)]
    lf[len(phns):][m] = lf[m]
    bt[ii,len(phns):][m] = np.nonzero(m)[0]
    m = lf[:len(phns)] < lpv + penalty
    lf[m] = lpv + penalty
    bt[ii][m] = lpi
    lf += lls[ii]
  path = [sil_index+len(lf)-len(phns)]
  for ii in  reversed(xrange(1,len(lls))):
    path.insert(0, bt[ii,path[0]])
  path = [phns[i] for i, junk in itertools.groupby(path) if i < len(phns)]
  return path

def levenshtein_distance(source, target, sub_cost=1, ins_cost=1, del_cost=1):
    target=np.array(target)
    dist = np.arange(len(target) + 1) * ins_cost
    for s in source:
        dist[1:] = np.minimum(dist[1:]+del_cost, dist[:-1] + (target != s) * sub_cost)
        dist[0] += del_cost
        for ii in range(len(dist)-1):
          if dist[ii+1] > dist[ii] + ins_cost:
             dist[ii+1] = dist[ii] + ins_cost
    return dist[-1]

def levenshtein_alignment(source, target, sub_cost=1, ins_cost=1, del_cost=1, empty_symbol=None):
    target=np.array(target)
    backtrack = np.ones((len(source)+1, len(target)+1))
    backtrack[0] = -1
    dist = np.arange(len(target) + 1) * ins_cost
    for ii, s in enumerate(source):
        cost4sub = dist[:-1] + (target != s) * sub_cost
        dist += del_cost
        where_sub = cost4sub < dist[1:]
        dist[1:][where_sub] = cost4sub[where_sub]
        backtrack[ii+1,1:][where_sub] = 0
        for jj in range(len(dist)-1):
          if dist[jj+1] > dist[jj] + ins_cost:
             dist[jj+1] = dist[jj] + ins_cost
             backtrack[ii+1,jj+1] = -1
    src_pos = len(source)
    tar_pos = len(target)
    alig=[]
    while tar_pos > 0 or src_pos > 0:
        where = backtrack[src_pos, tar_pos]
        if where >= 0: src_pos -= 1
        if where <= 0: tar_pos -= 1
        alig.insert(0, (empty_symbol if where < 0 else source[src_pos], 
                        empty_symbol if where > 0 else target[tar_pos]))
    return alig

def edit_stats_for_alignment(alig, empty_symbol=None):
  alig = np.array(alig)
  ncor = np.sum(alig[:,0]==alig[:,1])
  ndel = np.sum(alig[:,0]==np.array(empty_symbol))
  nphn = np.sum(alig[:,1]!=np.array(empty_symbol))
  nins = len(alig)-nphn  
  nsub = nphn - ncor - ndel
  return nphn, ncor, nins, ndel, nsub

def print_confusion_matrix(alig, phns, tab=4, empty_symbol=None):
  from collections import Counter
  conf_counts=Counter(map(tuple, alig))
  conf_mx = [[conf_counts[(row,col)] for row in list(phns)+[empty_symbol]] 
                                       for col in list(phns)+[empty_symbol]]
  print (" "*tab + (" %"+str(tab)+"s")*(len(phns)+1) % (tuple(phns)+ ('Del',)))
  for phn, row in zip(list(phns), conf_mx[:-1]):
    print ("%"+str(tab)+"s")%phn + (" %"+str(tab)+"s")*(len(phns)+1) % tuple(row)
  print (" "*(tab-3)+"Ins") + ((" %"+str(tab)+"s")*len(phns) % tuple(conf_mx[-1][:-1]))
