"""Recovery pacing and immutable metadata union, without cloud writes."""
import importlib.util
from pathlib import Path
import unittest


def module(name):
    p=Path(__file__).resolve().parents[1]/'src/utils/PDEBench'/name
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class RecoveryTests(unittest.TestCase):
    def test_five_workers_share_eighty_slots_per_hour(self):
        p=module('hf_commit_policy.py');events=[]
        for worker in range(1,6):
            now=100000.;last=None
            for _ in range(50):
                slot,t=p.next_commit_slot(now,worker,last)
                self.assertEqual(slot%5,worker-1)
                events.append((t,slot));now=t;last=slot
        events.sort();self.assertEqual(len({slot for _,slot in events}),len(events))
        for left,(start,_) in enumerate(events):
            within=sum(start<=t<start+3600 for t,_ in events[left:])
            self.assertLessEqual(within,80)
        self.assertGreaterEqual(min(b[0]-a[0] for a,b in zip(events,events[1:])),43)

    def test_retry_cooldown_never_reuses_attempted_slot(self):
        p=module('hf_commit_policy.py');slot,t=p.next_commit_slot(100000,1)
        newer,after=p.next_commit_slot(t,1,last_slot=slot,not_before=t+3600)
        self.assertGreater(newer,slot);self.assertGreaterEqual(after,t+3600)
        _,exclusive=p.next_commit_slot(t,1,last_slot=slot,exclusive=True)
        self.assertGreaterEqual(exclusive,t+45)
        with self.assertRaises(ValueError):p.next_commit_slot(100000,6)

    def test_current_budget_plus_five_twelve_hour_holds_fits(self):
        p=module('hf_commit_policy.py');self.assertEqual(p.planned_reservation_usd(),(.12191,.781324))
        with self.assertRaises(ValueError):p.planned_reservation_usd(prior=.5)

    def test_measured_remainder_includes_gate_and_merge_without_shrinking_to_budget(self):
        p=module('hf_commit_policy.py')
        self.assertEqual(p.measured_recovery_timeout_hours(6.6,26,.473042),9.5)
        self.assertEqual(p.planned_reservation_usd(hours=9.5,prior=.473042),(.09686,.957342))
        with self.assertRaisesRegex(ValueError,'exceeds USD 1'):
            p.measured_recovery_timeout_hours(6.6,26,.6)
        with self.assertRaisesRegex(ValueError,'exceeds one bounded cohort'):
            p.measured_recovery_timeout_hours(11,50,.1)

    def test_consolidation_preserves_exact_transport_and_rejects_changes(self):
        m=module('hf_partial_merge.py');old={'case-a':{'transport':{'path':'old'},'sha256':'a'}}
        new={'case-b':{'transport':{'path':'new'},'sha256':'b'}}
        self.assertEqual(set(m.validated_union(old,new)),{'case-a','case-b'})
        self.assertEqual(m.validated_union(old,old),old)
        with self.assertRaises(ValueError):m.validated_union(old,{'case-a':{'transport':{'path':'changed'},'sha256':'a'}})


if __name__=='__main__':unittest.main()
