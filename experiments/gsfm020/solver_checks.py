"""Unmodified parser round-trip checks extracted from Experiment16."""
import numpy as np
from matpower_case import read_case

def writecase(c,path):
 lines=['function mpc = input_case',"mpc.version = '2';",f"mpc.baseMVA = {c['baseMVA']};"]
 for k in ['bus','gen','branch','gencost']:lines += [f'mpc.{k} = [']+[' '.join(format(v,'.17g') for v in row)+';' for row in c[k]]+['];']
 path.write_text('\n'.join(lines)+'\n');parsed=read_case(path);assert all(parsed[k]==c[k] for k in ['bus','gen','branch','gencost','baseMVA'])

def checkparsed(c,raw):
 d=raw['parsed_network'];base=c['baseMVA'];load={};shunt={}
 for z in d.get('load',{}).values():load[z['load_bus']]=load.get(z['load_bus'],0)+complex(z['pd'],z['qd'])*base
 for z in d.get('shunt',{}).values():shunt[z['shunt_bus']]=shunt.get(z['shunt_bus'],0)+complex(z['gs'],z['bs'])*base
 for b in c['bus']:
  bid=int(b[0]);x=d['bus'][str(bid)];assert max(abs(x['vmin']-b[12]),abs(x['vmax']-b[11]),abs(load.get(bid,0)-complex(b[2],b[3])),abs(shunt.get(bid,0)-complex(b[4],b[5])))<1e-8
 for j,br in enumerate(c['branch'],1):
  x=d['branch'][str(j)]
  for k,want in [('br_r',br[2]),('br_x',br[3]),('tap',br[8] or 1),('shift',np.deg2rad(br[9])),('angmin',np.deg2rad(br[11])),('angmax',np.deg2rad(br[12])),('rate_a',br[5]/base),('br_status',br[10]),('f_bus',br[0]),('t_bus',br[1])]:assert abs(x.get(k,0)-want)<1e-9,(j,k,x.get(k),want)
  assert abs(x['b_fr']+x['b_to']-br[4])<1e-9
 for j,g in enumerate(c['gen'],1):
  x=d['gen'][str(j)]
  for k,want in [('pmin',g[9]/base),('pmax',g[8]/base),('qmin',g[4]/base),('qmax',g[3]/base),('gen_status',g[7]),('gen_bus',g[0])]:assert abs(x[k]-want)<1e-9
  rawcost=c['gencost'][j-1];n=int(rawcost[3]);expected=[v*base**(n-1-i) for i,v in enumerate(rawcost[4:4+n])];assert np.allclose(x['cost'],expected,rtol=0,atol=1e-7)
