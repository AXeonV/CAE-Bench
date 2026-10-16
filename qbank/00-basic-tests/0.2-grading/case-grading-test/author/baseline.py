"""Maintenance reference for the complete velocity echo task."""
import argparse
from caeoj.sdk import load_problem, write_result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    problem=load_problem(args.input)
    if problem.manifest.get('task')!='case-grading-test':
        raise ValueError('Expected case-grading-test')
    write_result(args.output,problem,{'velocity':problem.arrays['velocity'].copy()})

if __name__=='__main__':main()
