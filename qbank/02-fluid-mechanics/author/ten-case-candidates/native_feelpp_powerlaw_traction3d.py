"""Run the finite3D traction case from an immutable per-queue source bundle."""
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).parent/'feelpp-steady3d-traction16-bundle'))
import native_feelpp_powerlaw_first as producer

if __name__=='__main__':
    producer.CASE='ch02-2-1-7-06-power_law_traction'
    producer.RANKS=16
    producer.main()
