"""Task-specific entry to the shared author runner."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'navier-stokes-steady/author'))
from check import main
if __name__=='__main__':sys.exit(main(ROOT))
