"""Raw inverse-energy observations use the explicitly declared characteristic scale."""
import copy
from pathlib import Path
from caeoj_tools.grading_policy import author_policy
TASK=Path(__file__).resolve().parents[1]
def policy_for(problem):
    policy=copy.deepcopy(author_policy(TASK));p=problem.manifest['physics']['parameters']
    for phase in ['void','solid']:
        energy=p['atomic_volume']['value']*p[phase+'_energy_coefficient']['value']
        for suffix in ['coefficient','gradient','hessian']:
            policy['quantities'][phase+'_response_'+suffix]['rule']['atol']=1e-10/energy
    return policy
