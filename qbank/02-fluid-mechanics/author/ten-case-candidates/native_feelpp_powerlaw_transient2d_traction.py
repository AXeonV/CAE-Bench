"""Finite frozen2D transient traction, from the pinned native source bundle."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'feelpp-transient2d-bundle-v1'))
import native_feelpp_powerlaw_first as producer

if __name__=='__main__':
    producer.CASE='ch02-2-1-6-06-power_law_traction'
    producer.RANKS=8
    producer.main()
