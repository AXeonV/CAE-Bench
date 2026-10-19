"""Deterministic repository-wide commit slots for a frozen five-worker cohort.

Pure scheduling logic. The recovery transport must call this immediately before
POST /commit, not merely before a slow LFS preupload. No requests are sent here.
"""
import math


def next_commit_slot(server_now,worker,last_slot=None,not_before=0.,exclusive=False):
    if worker not in range(1,6):raise ValueError('Worker must be 1..5')
    if not all(math.isfinite(v) for v in (server_now,not_before)):
        raise ValueError('Finite server times required')
    instant=max(server_now,not_before)
    slot=math.floor(instant/46)
    if last_slot is not None:slot=max(slot,last_slot+1)
    while True:
        opening=slot*46+3
        closing=opening+3
        owned=exclusive or slot%5==worker-1
        if owned and max(instant,opening)<=closing:return slot,max(instant,opening)
        slot+=1


def planned_reservation_usd(rate_micro_usd=167,hours=12,workers=5,prior=.171774):
    if not 0<rate_micro_usd<=167 or workers!=5 or not .5<=hours<=12 or not 0<=prior<=1:
        raise ValueError('Unexpected approved recovery hardware or time ceiling')
    each=(math.ceil(hours*60)+10)*rate_micro_usd/1_000_000
    total=prior+workers*each
    if total>1:raise ValueError('Cumulative reservation exceeds USD 1')
    return round(each,6),round(total,6)


def measured_recovery_timeout_hours(estimated_work_hours, maximum_batches, prior,
                                    finalization_hours=1.75):
    """Budget a measured remainder, including the second commit's gate wait.

    Producer elapsed times stop before the verified POST; add half of the
    worker's 230-second slot period per batch, plus finalization and startup.
    Reject an unaffordable forecast instead of shrinking it to fit the money.
    """
    if (not math.isfinite(estimated_work_hours) or estimated_work_hours<0
            or type(maximum_batches) is not int or maximum_batches<1
            or not math.isfinite(finalization_hours) or finalization_hours<0):
        raise ValueError('Invalid measured recovery forecast')
    needed=estimated_work_hours+maximum_batches*115/3600+finalization_hours+.25
    hours=max(.5,math.ceil(needed*2)/2)
    if hours>12:raise ValueError('Measured remainder exceeds one bounded cohort')
    planned_reservation_usd(hours=hours,prior=prior)
    return hours
