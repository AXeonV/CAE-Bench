# reconstructed-energy-repair 独立考生审阅：考试材料模式

日期：2026-10-23。模式：exam-materials。题面结论：**本轮未发现未决题意问题**。样例状态：**两份全部公开输入、输出、参考数组已检查**。包内中性工具在主机可用；完整CFD与锁定镜像构建/运行仍未实测。

**最终包状态**：已对ZIP SHA256 `f58f517066bc84d24554c6c5fce429a7d3492b476c46c9ea8795df654ed0738d` 完成独立有界复核，结果见末节。下文保留初审1915包的原始记录；公开三文档/源码/驱动/网格/样例均与最终包逐字节相同，初审全数组证据可按摘要复用。

## 独立边界与冻结

仅使用公开三文件与 dist/reconstructed-energy-repair-agent.zip，未读该题私有/作者/隐藏/Oracle/修复材料，未接受答案解释，未编写solver或修复，未提交Git。模式与契约判断见 `../repair22-su22602-statements/report.md`。

ZIP完整SHA256：`1915e5399b7ae4a9287a5d9bf4bd8bb3c03935c4d41bb04af93785fe669731dc`。assembly：`0bd6a8ae46d9a08558a3eadb8989deafced20dd4bb97452aea5df1d37b87acce`。三文件工作树/包内逐字节一致，MANIFEST全部文件摘要匹配。公开依据为包内MANIFEST明确public_samples=[01,02]且实际提供两例input/output/reference；样例reference是公开判分资产，不是私有求解实现。

`evidence.json`保存ZIP及全部公开文件SHA、完整文本读取清单、两个源码包每个成员的SHA、完整SU2网格数值记录、所有HDF5全值及真实命令argv/cwd/退出码/stdout/stderr。公开快照位于package/。`audit_public.py`和`check_cfd_contract.py`是本次中性审阅代码，不含解答。

源码SU2 tar SHA256 `0d4e5f61475c5e9513da6c8653621587f4f8544820ae08da90039e3d8169fc59`，3032成员；MEL tar SHA256 `e0f7f95ab80d098a2c2bafceefb52e958378302c2150ef7cb9fe2bf4aa81177b`，12成员。全部普通成员完整字节读取/哈希，未运行其代码。独立public/common.hpp与SU2 archive中唯一指定common.hpp逐字节摘要相同，大小21763字节、SHA `f42a46bf2d40424bd4d1745e79f884b88d4657d97c3428e28a693afed19ca142`。未将全包哈希读取称作逐行语义审计整个SU2实现。

人工重点阅读了公开三文件、README/MANIFEST、配置、reconstruction-driver.cpp、run_case.py、read_vtk.py、任务验证扩展、两例problem.json和grading.json；全部其他公开文本完整读取记录到清单，公共框架通过包内工具消费。

## 固定CFD网格与配置

没有MSH；本题明确使用public/flatplate.su2而meshes={}。已逐行解析完整SU2文件：NDIME=2、13662个单元、13900个点；所有单元连接、节点坐标/编号和5个marker的每条边都在evidence.json.mesh中保存。节点编号逐行恰为0..13899。

|marker|边数|
|---|---|
|inlet|99|
|outlet|99|
|farfield|138|
|wall|99|
|symmetry|39|

wall包含100个唯一节点，按x递增后的节点身份已记录。由公开网格得到的float64 little-endian坐标SHA为node `7149ac0db1718f99c32201a02c769b48955aacaa85790d5425cc39da4c289ffd`、wall `842f50bba24c1bdef65f4e214c862cd546b299fed17e79b091748560a3a0cc80`，与公开任务扩展固定坐标摘要完全相符。

固定cfg声明RANS/SST、M=.2、Re=5e6、绝热wall和STANDARD_WALL_FUNCTION，保持真实配置；公开适配器只调整DATA声明的CFL、iterations+100、原生ASCII VTK格式及输出文件名。入口检查正常退出、最终rho/rhoE残差、完整步数、最后101记录CD稳定和全部有限值；按原生字段转换输出，没有重算焓、摩擦或能量。

为检查CFD问题族接口，另由**公开网格和DATA**构造仅用于结构检查的neutral-cfd-input：没有参考、求解或假造流场。五个CFD输出描述符、13900/100/1身份和坐标被公开validate-input接受，scope=task-contract。另以两点人工数值fixture真实运行公开read_vtk的scalar/vector解析，读回预设坐标/数组正确；这不证明真实SU2的VTK生产链已运行。

## 样例全量读取

两份problem.json字节完全相同，参数operation=0、d=2、gamma=1.4、R=287、kappa=1/3、relax=.8、muscl=1、limiter=0、cfl=400、iterations=2000。每例N=1，edge_ids=[0]、end_ids=[0,1]，times=float64[0]。逐dataset用[()]完整读取6个HDF5（两输入、两输出、两参考），没有省略任何数值数组或仅读首尾；全值在evidence.json.arrays。

每个输入有13个key：10个输入字段、edge_ids、end_ids、times。temperature/pressure/density/enthalpy为[1,2,1]；velocity、gradient_temperature、gradient_pressure为[1,2,2]；gradient_velocity、limiters为[1,2,4]；displacement为[1,1,2]。实体和时间轴身份与DATA一致。

两例T=[300,315] K、p=[101325,105000] Pa；rho=[1.1768292682926829,1.1614401858304297] kg/m^3，逐值恰等于p/(R*T)。两侧总焓包含相对当前平衡式的已有偏差，不能因EOS关系误删总焓阶段状态。样例01位移[.010426990235518425,.039942189962609356]；样例02位移[.033292344984807085,.011848812401119768]且左侧gradient_pressure=[-1e8,-1e8]，恰在合法梯度边界。

每个输出/公开参考恰含7个输出字段、end_ids、times；不含无需输出的edge_ids。7字段为temperature、velocity、pressure、density、enthalpy、momentum、energy；前五者与对应输入描述符一致且无sampling，momentum为[1,2,2]，energy为[1,2,1]。所有数组均float64/int64准确、全部有限、无属性/额外key，ID与times逐值复制。样例02的五个状态输出完整等于输入原状态；样例01发生重构。每例output/result.h5与reference/reference.h5的文件摘要也相同。此处描述原始公开数组，不据此认证参考计算正确。

## 真实工具运行及消费检查

复现命令（仓库根目录）：

```text
python runs/candidate-review/repair22-su22602-exam/audit_public.py
python runs/candidate-review/repair22-su22602-exam/check_cfd_contract.py
```

主机Windows/Python3.11，PYTHONPATH仅指向公开包src。未执行pip install，未宣称锁定依赖安装；info报告core_version=uninstalled，但assembly与task.reconstructed-energy-repair绑定正确。

两例各真实执行以下命令，S=01/02；精确argv/cwd与完整输出在evidence.json.commands：

```text
python -m caeoj info --input qbank/19-solver-repair/19.3-transport/reconstructed-energy-repair/samples/S/input/problem.json
python -m caeoj validate-input qbank/19-solver-repair/19.3-transport/reconstructed-energy-repair/samples/S/input/problem.json
python -m caeoj validate-output --input qbank/19-solver-repair/19.3-transport/reconstructed-energy-repair/samples/S/input/problem.json --output qbank/19-solver-repair/19.3-transport/reconstructed-energy-repair/samples/S/output/result.h5
python -m caeoj grade --input qbank/19-solver-repair/19.3-transport/reconstructed-energy-repair/samples/S/input/problem.json --output qbank/19-solver-repair/19.3-transport/reconstructed-energy-repair/samples/S/output/result.h5 --grading qbank/19-solver-repair/19.3-transport/reconstructed-energy-repair/samples/S/reference/grading.json
```

8条上述命令全部退出0，输入/输出valid=true、task-contract；两次grade均accepted/score=1。SDK真实load_problem/load_result后write_result并重新读取，各输出/身份/时间数组逐值完全相同。没有调用源码求解器生成新答案。

对每例7个输出字段分别只将最后一个标量值增加100，独立写副本并运行grade，共14个负例全部退出1/wrong_answer；证明每个声明字段参与评分。公开策略所有直接状态quantity均atol=1e-7、rtol=1e-10；CFD五quantity容差也与题面匹配，residuals采用atol=.5、rtol=0。CFD策略为公开配置中的可绑定分支；因没有公开CFD参考样例，本轮未实际执行该分支grade。

## 未完成验证与可选建议

两次真实调用公开run_case.py，使用其默认 `/opt/su2-build/bin/reconstruction-driver`；均在启动子进程时FileNotFoundError/WinError2退出1，没有产出actual结果。Windows主机不具备题目Linux路径，该失败属于本轮环境限制，不能据此判锁定镜像有缺陷。正式镜像中的离线依赖安装、Meson/Ninja构建、静态库链接、common.hpp替换重编、真实模板重构、完整CFD稳定性以及4CPU/8GiB/300秒/900秒预算均未实测。

本轮没有发现确认的公开材料障碍。可选建议为增加一个公开operation=1完整CFD样例，方便考生独立练习网格身份、真实日志及VTK输出链；现有两例均二维无限幅N=1，3D、点/边限幅和一阶也未由公开样例直接演示。该覆盖观察不等于题意缺陷，也不声称隐藏覆盖不足。

结论不外推为参考数值正确、方法验收完备、真实求解通过、资源达标或正式benchmark完成。后续ZIP或三文件改变需按SHA重新复核。

## 最终f58f包有界复核（2026-10-23）

独立从实际dist ZIP读取每一公开条目，与初审1915快照按完整字节比较；没有仅接受调用方的差异描述。最终SHA256为 `f58f517066bc84d24554c6c5fce429a7d3492b476c46c9ea8795df654ed0738d`。无增加/删除文件，仅4项改变：MANIFEST.json、pyproject.toml、src/caeoj_bundle/runtime.json、src/caeoj_task_ext/reconstruction.py。其余所有文件（包括三文档、public源码/driver、固定网格、两sample输入输出及公开参考）完整字节不变，MANIFEST所有新摘要正确。

pyproject仅bundle版本改为faf66911f5718a01；runtime仅assembly id改为 `faf66911f5718a014a88781cd13959e11a4a864a807a4ece1595c9eb46f7405f`。任务checker SHA256=`469c49923f6c8fb1c2318772351ae73a63e2a457474e296ae7ee1c466c6b4601`。checker唯一功能变化为在两operation共同路径要求type(iterations) is int，移除原仅op1、数值相等即可通过的检查。未改变求解模型、输出或评分条件。

实际执行 `python runs/candidate-review/repair22-su22602-exam/final_recheck.py`，完整旧新文件SHA/统一差异/14条命令及完整输出保存到final-recheck-evidence.json；最终公开快照在final-package/，未读取私有材料。

最终包两原样例分别info、validate-input、grade，共6条均退出0，task-contract绑定新assembly，grade仍accepted。类型变体使用op0公开样例及由公开网格/DATA构造的op1中性输入，均未运行求解器：

|iterations JSON值|op0|op1|
|---|---|---|
|2000（int）|合法，退出0|合法，退出0|
|3000（int）|合法，退出0|合法，退出0|
|2000.0（float）|E_RECONSTRUCTION，退出1|E_RECONSTRUCTION，退出1|
|true（bool）|E_SCHEMA，退出1|E_SCHEMA，退出1|

新的整数有效路径正常，浮点整数与布尔值被明确拒绝。三文档未变，未发现新增题意问题；初审材料/工具结论可在本差异范围内复用。此次仍没有锁定镜像安装、源码编译、模板/完整CFD运行或资源实测。
