# ---------------------------------------------------------------------------
# Minimal reproduction: Hysteretic zeroLength springs that carry NO load end a
# multi-step gravity analysis with tangent = E1*1e-9 (and stress = 0), because
# HystereticMaterial::setTrialStrain() returns early on |dStrain| < DBL_EPSILON
# without resetting Tstress/Ttangent/TloadIndicator to the committed values,
# so stress/tangent of an earlier (non-converged) trial get committed.
#
# Model: one RC column (fiber section) + cap beam + two bearings + deck link,
# with a Hysteretic "abutment-pile" spring in the transverse (z) direction at
# each deck node.  Gravity is vertical only, so the z-springs see only
# round-off noise (|strain| ~ 1e-17 .. 1e-13).
#
# Run:  OpenSees hysteretic_stale_tangent.tcl
# Units: kip, in.   Tested: OpenSees 3.8.0
# ---------------------------------------------------------------------------

proc buildAndRun {alg Pscale nSteps tol} {
    wipe
    model BasicBuilder -ndm 3 -ndf 6
    set D 63.0; set cov 3.0; set L 630.0; set B 98.0

    # RC column, circular fiber section
    uniaxialMaterial Concrete01 1 -4.9 -0.0045 -3.9 -0.015
    uniaxialMaterial Concrete01 2 -3.9 -0.002   0.0  -0.005
    uniaxialMaterial Steel01    3 58.0 29000.0 0.01
    uniaxialMaterial Elastic    4 1.0e8
    section Fiber 10 -torsion 4 {
        patch circ 1 20 8 0. 0. 0. [expr $D/2-$cov] 0. 360.
        patch circ 2 20 2 0. 0. [expr $D/2-$cov] [expr $D/2] 0. 360.
        layer circ 3 44 1.23 0. 0. [expr $D/2-$cov] 0. 360.
    }
    geomTransf PDelta 1 0 0 1
    geomTransf Linear 2 -1 0 0
    node 1 0. 0. 0.;  fix 1 1 1 1 1 1 1
    node 2 0. $L 0.
    element dispBeamColumn 1 1 2 5 10 1

    # cap beam: stiff elastic links (fictitious E/A/I, as commonly used)
    node 3 0. $L [expr -$B];  node 4 0. $L $B
    element elasticBeamColumn 11 3 2 1.0e8 1.0e9 1.0e9 1.0e8 1.0e9 1.0e9 2
    element elasticBeamColumn 12 2 4 1.0e8 1.0e9 1.0e9 1.0e8 1.0e9 1.0e9 2

    # bearings: Steel01 horizontal, very stiff vertical, soft rotational
    uniaxialMaterial Steel01  30 11.0 352.5 0.01
    uniaxialMaterial Elastic  31 1.0e10
    uniaxialMaterial Elastic  32 0.1
    node 5 0. $L [expr -$B];  node 6 0. $L $B
    mass 5 2.0 2.0 2.0 0. 0. 0.;  mass 6 2.0 2.0 2.0 0. 0. 0.
    element zeroLength 21 3 5 -mat 30 31 30 32 32 32 -dir 1 2 3 4 5 6
    element zeroLength 22 4 6 -mat 30 31 30 32 32 32 -dir 1 2 3 4 5 6
    element elasticBeamColumn 13 5 6 1.0e8 1.0e9 1.0e9 1.0e8 1.0e9 1.0e9 2

    # Hysteretic springs (abutment-pile backbone, pinching) in x and z -> zero force under gravity
    uniaxialMaterial Hysteretic 20 117.5 0.3 167.8 1.0 167.8 2.0 -117.5 -0.3 -167.8 -1.0 -167.8 -2.0 0.75 0.5 0 0 0.1
    node 7 0. $L [expr -$B];  fix 7 1 1 1 1 1 1
    node 8 0. $L $B;          fix 8 1 1 1 1 1 1
    element zeroLength 31 7 5 -mat 20 20 -dir 1 3
    element zeroLength 32 8 6 -mat 20 20 -dir 1 3

    # gravity: vertical only
    pattern Plain 1 Linear {
        load 5 0. [expr -1100.0*$Pscale] 0. 0. 0. 0.
        load 6 0. [expr -1100.0*$Pscale] 0. 0. 0. 0.
    }
    constraints Transformation; numberer RCM; system UmfPack
    test NormDispIncr $tol 200; algorithm $alg
    integrator LoadControl [expr 1.0/$nSteps]; analysis Static
    # step by step: detect "early return" steps whose committed stress nevertheless changed
    set ok 0; set nStale 0; set staleMsg ""
    set epsPrev [eleResponse 31 material 2 strain]; set sigPrev [eleResponse 31 material 2 stress]
    for {set k 1} {$k <= $nSteps} {incr k} {
        if {[analyze 1] != 0} { set ok 1 }
        set epsK [eleResponse 31 material 2 strain]; set sigK [eleResponse 31 material 2 stress]
        if {abs($epsK - $epsPrev) < 2.220446e-16 && $sigK != $sigPrev} {
            incr nStale
            if {$staleMsg eq ""} { set staleMsg [format "step %d: dStrain=%.1e (<DBL_EPSILON) but stress %.2e -> %.2e" $k [expr $epsK-$epsPrev] $sigPrev $sigK] }
        }
        set epsPrev $epsK; set sigPrev $sigK
    }
    loadConst -time 0.0

    # eigen on the post-gravity tangent (transverse mode of the deck mass on springs + column)
    wipeAnalysis; constraints Transformation; numberer RCM; system UmfPack
    set T1 [expr 2*3.14159265/sqrt([lindex [eigen -fullGenLapack 1] 0])]

    set eps [eleResponse 31 material 2 strain]
    set sig [eleResponse 31 material 2 stress]
    set kt  [eleResponse 31 material 2 tangent]
    return [list $ok $T1 $eps $sig $kt $nStale $staleMsg]
}

set E1 [expr 117.5/0.3]
foreach alg {KrylovNewton Newton} {
    puts "
=== algorithm $alg, 10 gravity steps, NormDispIncr 1e-8.  z-spring 31 (E1 = [format %.2f $E1] kip/in) ==="
    puts [format "%6s %4s %8s  %11s %11s %11s  %6s  %s" P ok T1(s) strain stress tangent stale note]
    set nBad 0; set nRun 0; set nRunStale 0
    for {set i 50} {$i <= 150} {incr i 2} {
        set P [expr $i/100.0]
        lassign [buildAndRun $alg $P 10 1.0e-8] ok T1 eps sig kt nStale staleMsg
        incr nRun
        if {$nStale > 0} { incr nRunStale }
        set note ""
        if {$kt < 1.0} { incr nBad; set note "<-- tangent = E1*1e-9, stress = 0 (spurious)" }
        if {$note ne "" || $i % 10 == 0} {
            puts [format "%6.2f %4d %8.3f  %+11.3e %+11.3e %11.3e  %6d  %s" $P $ok $T1 $eps $sig $kt $nStale $note]
            if {$staleMsg ne ""} { puts "                  first stale commit: $staleMsg" }
        }
    }
    puts "  -> runs with >=1 stale commit (strain unchanged within DBL_EPSILON, committed stress changed): $nRunStale of $nRun"
    puts "  -> runs ending in the spurious zero-tangent state: $nBad of $nRun"
}
