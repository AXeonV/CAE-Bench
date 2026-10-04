"""Private recipes; none of these case labels or reference formulas are public input."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    name: str
    family: str = 'channel'
    n: int = 32
    size: tuple = (1.0, 1.0)
    origin: tuple = (0.0, 0.0)
    rho: float = 1.0
    nu: float = 0.01
    lower: float = 0.0
    upper: float = 0.0
    acceleration: float = 0.0
    axis: int = 0
    initial: str = 'zero'
    amplitude: float = 1.0
    drift: tuple = (0.0, 0.0)
    mode: int = 1
    phase: tuple = (0.0, 0.0)
    lid: str = 'top'
    lid_sign: int = 1
    pattern: str = 'vortex'
    coefficients: tuple = ()
    wave: tuple = (1, 2)
    epochs: tuple = (0.0, 0.001, 0.003, 0.01, 0.03, 0.1, 0.3)
    sparse: bool = False
    binary: bool = False


STEADY = [
    Case('01-rest', n=4),
    Case('02-couette', upper=1),
    Case('03-poiseuille', acceleration=0.08),
    Case('04-couette-poiseuille', n=64, upper=0.6, acceleration=0.032),
    Case('05-reverse-pressure-drive', acceleration=-0.08),
    Case('06-counter-moving-walls', lower=-0.6, upper=0.6),
    Case('07-vertical-channel', axis=1, upper=0.5, acceleration=0.04),
    Case('08-long-shifted-channel', origin=(-1, 2), size=(2, 0.5), nu=0.005, upper=0.8),
    Case('09-sparse-binary-channel', n=48, sparse=True, binary=True, acceleration=0.08),
    Case('10-density-viscosity', rho=2, nu=0.02, acceleration=0.16),
    Case('11-low-re-channel', nu=0.05, upper=1),
    Case('12-opposing-shear-and-drive', upper=-0.4, acceleration=0.094),
    Case('13-cavity-32', family='cavity', upper=1),
    Case('14-cavity-48', family='cavity', n=48, upper=1),
    Case('15-cavity-64-binary', family='cavity', n=64, upper=1, sparse=True, binary=True),
    Case('16-cavity-scaled-shifted', family='cavity', n=48, upper=0.5,
         size=(2, 2), origin=(1, -2), rho=2, nu=0.01),
    Case('17-zero-net-flux', n=48, lower=-0.4, upper=-0.4, acceleration=0.048),
    Case('18-interior-reversal', n=64, lower=-0.7, upper=0.2, acceleration=0.08),
    Case('19-moving-both-driven', n=48, lower=0.3, upper=0.7, acceleration=-0.064),
    Case('20-vertical-negative', n=48, axis=1, lower=-0.2, upper=-0.8, acceleration=0.032),
    Case('21-wide-cross-section', n=64, size=(0.5,2), nu=0.02, lower=-0.6, upper=0.6),
    Case('22-thin-driven-channel', n=48, size=(2,0.5), nu=0.005, rho=0.5, acceleration=0.12),
    Case('23-weak-drive', n=16, nu=0.05, lower=0.002, upper=-0.003, acceleration=0.0004),
    Case('24-asymmetric-shifted', n=24, origin=(-2,-1), size=(0.5,1), nu=0.02,
         lower=0.4, upper=-0.2, acceleration=-0.04, sparse=True, binary=True),
    Case('25-cavity-top-reverse', family='cavity', n=48, upper=1, lid_sign=-1),
    Case('26-cavity-bottom-positive', family='cavity', n=48, upper=1, lid='bottom'),
    Case('27-cavity-bottom-negative', family='cavity', n=48, upper=1, lid='bottom', lid_sign=-1),
    Case('28-cavity-left-positive', family='cavity', n=48, upper=1, lid='left'),
    Case('29-cavity-left-negative', family='cavity', n=64, upper=1, lid='left', lid_sign=-1),
    Case('30-cavity-right-positive', family='cavity', n=48, upper=1, lid='right', binary=True),
    Case('31-cavity-right-negative', family='cavity', n=64, upper=1, lid='right', lid_sign=-1, sparse=True),
    Case('32-cavity-small-shifted', family='cavity', n=48, upper=1, lid='bottom', lid_sign=-1,
         size=(0.5,0.5), origin=(-2,1.5), nu=0.005, rho=0.5, sparse=True, binary=True),
]

TRANSIENT = [
    Case('01-rest', n=4),
    Case('02-start-couette', upper=1),
    Case('03-start-poiseuille', acceleration=0.08),
    Case('04-start-combined', n=48, upper=0.6, acceleration=0.032),
    Case('05-reverse-drive', acceleration=-0.08),
    Case('06-start-counter-walls', lower=-0.6, upper=0.6),
    Case('07-stop-shear', initial='linear'),
    Case('08-decay-multiple-modes', initial='modes'),
    Case('09-signed-piecewise-profile', n=64, initial='plate'),
    Case('10-vertical-start', axis=1, upper=0.5, acceleration=0.04),
    Case('11-shifted-sparse-binary', n=48, size=(2, 0.5), origin=(-1, 2),
         nu=0.005, upper=0.8, sparse=True, binary=True),
    Case('12-fast-viscous-start', rho=2, nu=0.05, upper=1),
    Case('13-periodic-vortex', family='periodic', n=32,
         epochs=(0, 0.01, 0.03, 0.1, 0.3, 1.0)),
    Case('14-advected-vortex', family='periodic', n=32, drift=(0.7, 0), nu=0.017,
         epochs=(0, 0.01, 0.03, 0.1, 0.3, 1.0)),
    Case('15-oblique-advection', family='periodic', n=48, drift=(0.4, -0.3),
         nu=0.015, phase=(0.3, 0.7), epochs=(0, 0.01, 0.04, 0.12, 0.4, 1.0)),
    Case('16-two-wave-vortex', family='periodic', n=64, mode=2, amplitude=0.6,
         drift=(-0.2, 0.3), nu=0.011, epochs=(0, 0.005, 0.015, 0.05, 0.15, 0.4)),
    Case('17-scaled-density-vortex', family='periodic', n=48, size=(2, 2),
         origin=(1, -2), rho=2, nu=0.036, amplitude=1.2, drift=(0.3, 0.3),
         phase=(0.4, -0.2), epochs=(0, 0.01, 0.04, 0.12, 0.4, 1.0)),
    Case('18-sparse-binary-vortex', family='periodic', n=48, sparse=True, binary=True,
         drift=(-0.4, 0.2), nu=0.016, phase=(-0.2, 0.6),
         epochs=(0, 0.01, 0.03, 0.1, 0.3, 1.0)),
    Case('19-driven-nonzero-initial', n=64, initial='modes', lower=0.2, upper=-0.4,
         acceleration=0.08, nu=0.015, epochs=(0,.001,.002,.006,.017,.043,.11,.3)),
    Case('20-vertical-local-pulse', n=64, axis=1, initial='pulse', upper=-0.4,
         acceleration=0.03, origin=(1,-2), rho=0.5),
    Case('21-oscillatory-counter-drive', n=64, initial='oscillatory', lower=-0.3,
         upper=0.3, acceleration=-0.04, epochs=(0,.001,.0017,.004,.013,.057,.16,.3)),
    Case('22-reverse-initial-shear', n=48, initial='reverse', lower=0.6, upper=-0.2,
         acceleration=0.04, nu=0.02),
    Case('23-double-local-pulses', n=64, initial='double_pulse', size=(2,.5),
         nu=0.005, rho=2, lower=-0.2, upper=0.4, sparse=True, binary=True),
    Case('24-initial-counter-walls', n=48, initial='modes', lower=-0.8, upper=0.8,
         acceleration=-0.016, size=(.5,2), nu=0.02),
    Case('25-mixed-vortex-matrix', family='periodic', n=48, nu=0.025,
         coefficients=(.7,.2,-.3,.5), drift=(.4,-.2), phase=(.2,.5),
         epochs=(0,.005,.012,.027,.061,.14,.33,.8)),
    Case('26-mixed-two-wave', family='periodic', n=64, mode=2, nu=0.02,
         coefficients=(.3,-.2,.25,.35), drift=(-.4,.3), phase=(-.4,.8),
         epochs=(0,.005,.009,.02,.043,.09,.18,.4)),
    Case('27-mixed-scaled-density', family='periodic', n=48, size=(2,2), origin=(-2,1),
         rho=2, nu=0.04, coefficients=(.4,.3,.2,-.5), drift=(.2,.2),
         epochs=(0,.005,.014,.04,.11,.31,.65,1)),
    Case('28-mixed-sparse-binary', family='periodic', n=64, sparse=True, binary=True,
         nu=0.025, coefficients=(.55,-.4,.3,.2), drift=(.3,-.3), phase=(.6,-.3),
         epochs=(0,.005,.011,.029,.073,.18,.43,.7)),
    Case('29-oblique-periodic-shear', family='periodic', pattern='shear', wave=(1,2),
         n=48, amplitude=.8, drift=(.5,-.2), nu=.015, phase=(.4,0),
         epochs=(0,.005,.015,.04,.1,.25,.6,1)),
    Case('30-crosswise-periodic-shear', family='periodic', pattern='shear', wave=(2,-1),
         n=48, amplitude=.7, drift=(-.4,.6), nu=.015, rho=2, phase=(-.7,0),
         epochs=(0,.005,.017,.053,.12,.28,.55,1)),
    Case('31-horizontal-periodic-shear', family='periodic', pattern='shear', wave=(0,2),
         n=32, amplitude=.9, drift=(.2,.4), nu=.014, size=(.5,.5), origin=(2,-2),
         epochs=(0,.005,.012,.029,.075,.19,.47,1)),
    Case('32-diagonal-periodic-shear', family='periodic', pattern='shear', wave=(1,-1),
         n=64, amplitude=.8, drift=(.35,.35), nu=.015, sparse=True, binary=True,
         phase=(1.1,0), epochs=(0,.005,.013,.037,.093,.21,.48,1)),
]


def time_scale(case):
    return case.size[1-case.axis]**2/case.nu if case.family == 'channel' else case.size[0]


def cases(transient):
    return TRANSIENT if transient else STEADY
