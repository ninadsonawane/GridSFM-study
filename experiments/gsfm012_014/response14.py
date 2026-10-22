from electrical import *
O=R/'results/comparisons/GSFM-014/20261023-rated-variants';relevant=[];context=[]
for net in ['300','600']:
 RD=O/('R'+net+'-base');UD=O/('U'+net+'-base');c=read(RD/'input.json');ref=terms(c,read(RD/'ac-native.json'));uref=terms(c,read(UD/'ac-native.json'));rs=np.maximum(abs(ref['sf']),abs(ref['st']));us=np.maximum(abs(uref['sf']),abs(uref['st']));selected=[i for i,b in enumerate(c['branch']) if b[5]-rs[i]<=max(.1,.001*b[5]) or us[i]-b[5]>1e-3]
 for method,file in [('AC-OPF','ac-native.json'),('microsoft-v1.1','microsoft-v1.1-native.json'),('newer-base-v2','newer-base-v2-native.json')]:
  r=terms(c,read(RD/file));u=terms(c,read(UD/file));a=np.maximum(abs(r['sf']),abs(r['st']));b=np.maximum(abs(u['sf']),abs(u['st']))
  for j in selected:
   desired=rs[j]-us[j];actual=a[j]-b[j];relevant.append({'network':net,'method':method,'branch_row_1based':j+1,'from_bus':int(c['branch'][j][0]),'to_bus':int(c['branch'][j][1]),'rateA':c['branch'][j][5],'reference_delta_maxS_R_minus_U':float(desired),'method_delta_maxS_R_minus_U':float(actual),'delta_error_MVA':float(actual-desired),'direction_agrees_when_reference_change_gt_0_1':None if abs(desired)<=.1 else bool(actual*desired>0),'R_final_ratio':float(a[j]/c['branch'][j][5])})
for item in read(O/'scenario-manifest.json')['scenarios']:
 if not item['id'].startswith('R'):continue
 D=O/item['id'];c=read(D/'input.json');ids,b,e,f,t=matrices(c);ref=read(D/'ac-native.json') if (D/'ac-native.json').exists() else None
 for rel in ['microsoft-v1.1','newer-base-v2']:
  s=read(D/(rel+'-native.json'));tr=terms(c,s);maxs=np.maximum(abs(tr['sf']),abs(tr['st']))
  for j,z in enumerate(c['branch']):
   if maxs[j]-z[5]<=1e-3:continue
   a,bb=f[j],t[j];context.append({'scenario':item['id'],'release':rel,'branch_row_1based':j+1,'from_bus':int(z[0]),'to_bus':int(z[1]),'r':z[2],'x':z[3],'tap':z[8] or 1,'rateA':z[5],'maxS':float(maxs[j]),'ratio':float(maxs[j]/z[5]),'Vm_from':s['vm'][a],'Vm_to':s['vm'][bb],'Vm_error_from':None if ref is None else s['vm'][a]-ref['vm'][a],'Vm_error_to':None if ref is None else s['vm'][bb]-ref['vm'][bb],'angle_difference_error_deg':None if ref is None else (s['va_deg'][a]-s['va_deg'][bb])-(ref['va_deg'][a]-ref['va_deg'][bb]),'from_P_residual':float(tr['r'][a].real),'from_Q_residual':float(tr['r'][a].imag),'to_P_residual':float(tr['r'][bb].real),'to_Q_residual':float(tr['r'][bb].imag)})
csvsave(O/'reference-relevant-rating-response.csv',relevant);csvsave(O/'overload-electrical-context.csv',context);print('RELEVANT COUNTS',len(relevant),'OVERLOAD CONTEXT',len(context))
