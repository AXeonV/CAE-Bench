"""Generate the deliverable environment from the single maintained template."""
import json,shutil,subprocess,tomllib,zipfile
from pathlib import Path
ROOT=Path('D:/Code/CAE-Bench-OJ');WORK=ROOT/'runs/releases/rc6-authoring'
RELEASE=ROOT/'runs/releases/caeoj-qbank-20261024-rc6';ENV=RELEASE/'environment';ENV.mkdir()
catalog=json.loads((RELEASE/'catalog.json').read_text(encoding='utf-8'))
requirements=set()
for task in catalog['tasks']:
    with zipfile.ZipFile(RELEASE/task['public_archive']) as archive:
        requirements.update(tomllib.loads(archive.read('pyproject.toml').decode())['project']['dependencies'])
requirements.update(['scipy==1.18.1','setuptools==84.2.1','wheel==0.48.0','packaging==26.3'])
(ENV/'requirements.txt').write_text('\n'.join(sorted(requirements))+'\n',encoding='utf-8')
source=ROOT/'src/utils/harbor/environment'
for name in ['check_environment.py','install_and_check.py','build_runtime.py','check_tasks.py']:
    shutil.copyfile(source/name,ENV/name)
image=json.loads(subprocess.check_output(['docker','image','inspect','python:3.14-slim'],text=True))[0]
base=next(d for d in image['RepoDigests'] if d.startswith('python@sha256:'))
prefix=(source/'Dockerfile').read_text(encoding='utf-8').split('COPY agent.zip')[0]
assert 'python:3.14-slim' in prefix
prefix=prefix.replace('python:3.14-slim',base)
dockerfile=prefix+'''COPY requirements.txt /tmp/requirements.txt
COPY check_environment.py install_and_check.py /opt/caeoj/
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt \\
    && python -m pip check \\
    && python /opt/caeoj/check_environment.py
ENV PIP_NO_INDEX=1 PIP_DISABLE_PIP_VERSION_CHECK=1
CMD ["bash"]
'''
(ENV/'Dockerfile').write_text(dockerfile,encoding='utf-8',newline='\n')
config={'image':'caeoj-runtime:20261024-rc6','platform':'linux/amd64','base_image':base,
        'binary_image_included':False,'initial_build_requires_network':True,'runtime_install_network_required':False,
        'shared_template':'src/utils/harbor/environment/Dockerfile'}
(ENV/'runtime.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
(ENV/'README.md').write_text('''# RC6 科学计算环境

RC5遗漏了71份题内harbor/requirements.txt，其中69份包含SciPy。RC6已恢复这些既有文件，并交付统一科学环境构建配方。题面、DATA、647个正式case的输入／参考／评分、资源和96个随机格式样例均保持RC5；不更正历史成绩。

## 构建和检查

从发行根目录运行：

```sh
python release.py verify
python environment/build_runtime.py
python environment/check_tasks.py --jobs 2 --output ../rc6-environment-checks
```

需要Docker的Linux AMD64容器支持。首次构建联网下载固定基础镜像、Debian系统包和固定Python依赖；本包不分发预建镜像二进制。Docker构建配方和Python锁随包提供，实际验证使用的基础digest、镜像ID和版本见runtime.json及validation.json。Debian仓库包版本可能随构建日期变化，所以跨机器重新构建仍须执行检查，不能仅凭镜像标签认定环境等价。

运行基底提供Python 3.14、NumPy、SciPy、h5py、Gmsh、jsonschema，及C++、OpenMP、Open MPI、HDF5开发库和所需系统动态库。协议依赖与各公开包的精确锁一致；setuptools/wheel/packaging供离线安装公开包使用，SciPy属于执行环境而非协议核心依赖。

check_tasks.py对每题各启动两个互不复用的全新容器，分别标记candidate与verifier，均为network=none。分别离线安装该题公开包及本题harbor/requirements.txt，执行pip check、严格provider绑定检查、Python模块实际导入、SciPy稀疏求解、h5py读写、Gmsh初始化、C++/OpenMP两线程、原生HDF5建文件重开以及MPI双rank归约。验证的是安装和环境功能，不执行模型、不读取隐藏参考计算答案、不更正历史成绩，不代表参考数值资格或正式资源达标。

检查单题可用 `python environment/check_tasks.py --task TASK --output ../rc6-single-check`。输出目录必须在发行目录之外，以免改变发行完整性清单。检查结果包含独立container ID、镜像ID、逐题requirements摘要、provider和实际库版本；已存在checkpoint时会拒绝覆盖，请换新输出目录。

## 使用公开材料

考生只接收public目录对应的Agent ZIP。解压到单独的公开工作目录，然后在本运行基底的新容器中安装该目录：

```sh
python -m pip install --no-index --no-build-isolation /path/to/public-package
python -m pip check
python -m caeoj info
```

这些命令在容器内执行。公开包各自严格绑定一题，不能将多题依次覆盖安装到同一容器。基底构建完成后安装不需要网络，默认PIP_NO_INDEX=1。对应环境requirements已在RC6完整题目中交付；已有依赖满足其约束，检查脚本实际核验这一点。

## 维护方与独立判题

`python release.py extract TASK ../empty-task-workspace`合并公开SDK与本题私有材料，仅供维护方。提取后的`<catalog.path>/harbor/requirements.txt`（若存在）必须在考生及独立判题环境中均被消费；源码附件的prepare_harbor.py已修复这一消费链，并在两个Docker构建上下文安装后运行同源环境探针。判题容器须独立启动且无网络，不复用考生执行后修改过的容器；只传入冻结提交，不能把包含reference的完整工作目录给考生。

实际Harbor Agent凭据、模型适配器和求解器实现不随本包提供，仍沿用维护方既有工具。这里提供完整数据、环境配方及安装验证，不宣称所有第三方系统软件完全离线分发。
''',encoding='utf-8')
print('Environment recipe prepared with pinned Python dependency closure and source-derived system setup',flush=True)
