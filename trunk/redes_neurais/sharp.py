from math import exp

def norm_ent(ent) :
  a = []
  for i in ent:
  	a.append( (i -86.71)/(549 - 86.71) );
  return a;

def desn_sai(sai) :
  a = []
  for i in sai:
  	a.append( i * (100 - 4) + 4 );
  return a;

def sharp_neural(ent):
  ent = norm_ent([ent])
  #ent = [ent]
  b = [
  	[-5.5558,-0.4723],
  	[3.6367 * 10 ** 04]
  ]
  IW = [
  	[-3.2951],[-38.7308]
  ]
  LW = [
  	[3.6365 * 10 ** 4,0.0002* 10 ** 4]
  ]
  neuronios = 2
  saidas    = 1
  
  def purelin(n) : return n
  def logsig(n)  : return 1 / (1 + exp(  -n))
  def tansig(n)  : return 2 / (1 + exp(-2*n))-1
  
  transferc1  = tansig
  transferout = tansig
  	
  c1 = [0 for i in range(neuronios)]
  
  for j in range(neuronios):
  	for i in range(len(ent)):
  		c1[j] += IW[j][i] * ent[i]
  	c1[j] = transferc1(b[0][j]+ c1[j]);
  
  # passei da primeira camada
  # fim
  out = [0 for i in range(saidas)]
  for j in range(saidas):
  	for i in range(neuronios):
  		out[j] += LW[j][i] * c1[i]
  	out[j] = transferout(out[j]+b[1][j])
  return desn_sai(out)[0];
  #return out[0]

if __name__ == '__main__' :
  while 1:
    ent = input(': ')
    print sharp_neural(ent)
