from copy import deepcopy
import torch
# create two sample vectors
def f(inps, d):
    return torch.cat((inps, d.unsqueeze(2)), dim=-1)

inps = torch.randn([64, 161, 1])
d = torch.randn([64, 161])

assert addTensor(deepcopy(inps), deepcopy(d)).equal(f(inps, d))