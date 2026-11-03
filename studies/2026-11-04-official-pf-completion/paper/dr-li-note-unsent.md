# Draft for Dr. Li - not sent

Dr. Li,

I reused the same 59 loading inputs and checked AC/DC references, then added the released V2 Newton completion and the compatible case500 adapted checkpoint.

Frozen V2 completion converged on 4/59 inputs. The adapted case500 version converged on 15/15, but none passed all original operating limits. An exact-matrix check removed the small graph-physics balance discrepancy without removing the generator/voltage violations.

The useful distinction is in the response: adapted PF corrected the aggregate Q-response sign and improved direction agreement, but Q-response RMSE became worse than the adapted native output. Q-only +10% loading also exposed a branch overload absent from the tested combined-loading path. The original case-3 effect is explained in the native output; neither PF endpoint converged, so I have not presented it as a completed operating response.

The draft treats this as a reproducible deployment audit. PF leaving inequalities violated is already known, and I have not claimed a new method or established broad novelty. The next decision is whether these stage-specific findings are strong enough for the five-page PES paper.

Ninad
