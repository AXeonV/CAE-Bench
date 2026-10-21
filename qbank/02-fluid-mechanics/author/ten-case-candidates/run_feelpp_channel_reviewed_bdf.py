"""Finite reviewed channel checkpoint continuation, maxdt0.02, original4h deadline."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'feelpp-reviewed-channel-reuse-bundle-v1'))
import resume_channel,continue_channel
if __name__=='__main__':
    resume_channel.main()
    root=Path(sys.argv[sys.argv.index('--root')+1]);state=json.loads((root/'cases'/resume_channel.CASE/'status.json').read_text())
    if state['status']=='native_checkpoint_pending_continuation':continue_channel.main()
