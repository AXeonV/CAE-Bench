"""Pack the genuine upstream build closure, excluding unrelated applications/tests."""
from pathlib import Path
import tarfile
from prepare_source import SOURCE,TASK


def main():
    target=TASK/'public/kratos-source.tar.gz'
    with tarfile.open(target,'w:gz',compresslevel=6) as tar:
        for item in sorted(SOURCE.rglob('*')):
            rel=item.relative_to(SOURCE)
            if not item.is_file():continue
            parts=rel.parts
            if any(v in {'tests','benchmarks','.github','.git','__pycache__'} for v in parts):continue
            if parts[0]=='applications' and len(parts)>1 and parts[1]!='StructuralMechanicsApplication':continue
            if parts[0] in {'documents','docs'}:continue
            tar.add(item,arcname=str(rel).replace('\\','/'),recursive=False)
    print(target,target.stat().st_size)
if __name__=='__main__':main()
