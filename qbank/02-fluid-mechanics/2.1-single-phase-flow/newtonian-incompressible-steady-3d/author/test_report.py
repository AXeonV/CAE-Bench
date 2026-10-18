"""Check native log interpretation and report provenance without solver runs."""
import json
from pathlib import Path
import tempfile
import unittest

import report


class ReportTests(unittest.TestCase):
    def test_elmer_linear_residual_is_not_nonlinear_or_steady_change(self):
        text='''NAVIER-STOKES ITERATION 14
  3 0.3E-11
Relative Change : 1.5E-9
NAVIER-STOKES ITERATION 15
  1 0.5E-6
  31 0.7817E-11
  31 0.7817E-11
Relative Change : 4.7E-10
ComputeChange: SS (ITER=1) (NRM,RELC): ( 0.2 2.0 )
'''
        r=report.parse_log('elmer',text)
        self.assertEqual(r['outer_iteration'],15)
        self.assertEqual(r['last_linear_iteration'],31)
        self.assertAlmostEqual(r['final_linear_residual'],7.817e-12)
        self.assertAlmostEqual(r['absolute_nonlinear_update'],4.7e-10)

    def test_foam_keeps_multiple_pressure_solves_and_initial_residuals(self):
        text='''Time = 1
smoothSolver: Solving for Ux, Initial residual = 1, Final residual = 0.01, No Iterations 5
Time = 925
smoothSolver: Solving for Ux, Initial residual = 2e-11, Final residual = 1e-13, No Iterations 3
DICPCG: Solving for p, Initial residual = 3e-10, Final residual = 4e-12, No Iterations 12
DICPCG: Solving for p, Initial residual = 4e-12, Final residual = 4e-12, No Iterations 0
time step continuity errors : sum local = 3e-14, global = -2e-17, cumulative = 1e-15
SIMPLE solution converged in 925 iterations
'''
        r=report.parse_log('openfoam',text)
        self.assertEqual(r['outer_iteration'],925)
        self.assertTrue(r['simple_converged'])
        self.assertEqual([s['iterations'] for s in r['linear_solves_last_outer']],[3,12,0])
        self.assertEqual(r['linear_solves_last_outer'][1]['initial_residual'],3e-10)
        self.assertEqual(r['continuity']['global'],-2e-17)

    def test_absent_metrics_are_not_zero(self):
        for solver in ['elmer','openfoam']:
            self.assertIsNone(report.parse_log(solver,'')['outer_iteration'])
        self.assertEqual(report.fmt(None),'—')

    def test_failure_summary_uses_last_attempt_and_separates_margin(self):
        case=dict(case='052-periodic-duct-14',status='failed',attempts=[
            dict(solvers=[dict(exit_code=124)],cross_score=0),
            dict(solvers=[dict(exit_code=0)],cross_score=1)])
        self.assertEqual(report.failure_reason(case),'参考精度余量不足')
        text='\n'.join(report.summary_lines(dict(cases=[case])))
        self.assertIn('| periodic-duct | 1 | 0 | 1 | 0 |',text)
        self.assertNotIn('| 原生求解超时 |',text)
        case['attempts'][-1]=dict(solvers=[dict(exit_code=124,timed_out=True)])
        self.assertEqual(report.failure_reason(case),'原生求解超时')
        case['attempts'][-1]=dict(solvers=[dict(exit_code=1)])
        self.assertEqual(report.failure_reason(case),'原生求解异常退出')
        case['attempts'][-1]=dict(solvers=[dict(exit_code=0)],cross_score=0)
        self.assertEqual(report.failure_reason(case),'交叉判分未通过')

    def test_reused_run_keeps_historical_budget_and_host_path(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);work=root/'production';folder=work/'native/case/old/elmer-n12'
            folder.mkdir(parents=True)
            (folder/'flow.log').write_text('NAVIER-STOKES ITERATION 2\n 5 1e-12\nRelative Change : 1e-10\n')
            (folder/'flow.sif').write_text('Nonlinear System Max Iterations = 100\n Linear System Max Iterations = 3000\n')
            solvers=root/'solvers';receipt=solvers/'local/runs/elmer/old-id/record.json';receipt.parent.mkdir(parents=True)
            record=dict(id='old-id',workdir=str(folder),resources=dict(cpus=4,memory='4g',timeout=600),seconds=12.5,exit_code=0)
            receipt.write_text(json.dumps(record))
            binding=dict(reused_native_run='old-id',command=['docker','run','--workdir','/work'])
            result=report.run_metrics(work,solvers,'case','new',12,'elmer',binding)
            self.assertEqual(result['actual_budget']['timeout'],600)
            self.assertEqual(result['wall_seconds'],12.5)
            self.assertEqual(result['iteration_limits'],dict(outer=100,linear=3000))
            self.assertTrue(result['reused'])
            self.assertIsNotNone(result['log_sha256'])

    def test_old_success_is_not_current_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);work=root/'production';case=work/'generated/cases/case'
            case.mkdir(parents=True);(case/'problem.json').write_text(json.dumps(dict(outputs={})))
            evidence=work/'evidence';evidence.mkdir();(evidence/'case.json').write_text(json.dumps(dict(code_id='old',passed=True,attempts=[])))
            (root/'batch.log').write_text('')
            state=dict(code_id='current',stdout_log='batch.log',workers=20,author_budget=dict(cpus=2,memory='4g',timeout=3600))
            scheduler=root/'scheduler.json';scheduler.write_text(json.dumps(state))
            result=report.collect(work,root/'solvers',scheduler)
            self.assertEqual(result['completed'],0)
            self.assertEqual(result['cases'][0]['status'],'incomplete')
            self.assertEqual(result['cases'][0]['attempts'],[])


if __name__=='__main__':unittest.main(verbosity=2)
