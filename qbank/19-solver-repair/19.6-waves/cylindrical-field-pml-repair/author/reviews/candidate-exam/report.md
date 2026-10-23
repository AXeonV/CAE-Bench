# cylindrical-field-pml-repair 独立考生审阅：考试材料模式

日期2026-10-23。模式exam-materials。题面结论：**本轮未发现未决题意问题**。样例状态：**两例全部公开输入、输出、样例参考数组和MSH已检查**。公开包中性工具可消费；正式镜像安装/构建/FDTD/资源实测未完成。

## 边界与完整性

独立性和三文档要求判断见 `../repair22-meep2338-statements/report.md`。没有读作者答案、修复、私有参考或其他审阅记录；仅对包内明示公开的样例检查资产运行grade，不执行参考求解器。

ZIP完整SHA256=`acac8a89d2b02b4aa1a753fcdd2354b836c2af0af1cb21748973ed41564e0027`；assembly=`61115e8cbd67ade8b9c53865f25e6b892840a01a0b8061236869cf3451872c47`。MANIFEST全部文件摘要匹配，包内三文档与工作树逐字节相同。所有文件SHA、完整文本读取清单、6份HDF5全数组、2份MSH全文及解析后几何/拓扑、精确命令及完整输出保存在evidence.json；公开快照在package/。

源码tar.gz SHA256=`796b8ecc813382251c26a2830c461ac9c6be3cda4f7aae6d2409ba9ff7ac7fdb`。728个成员已遍历，普通文件完整字节读取并记录SHA，未执行。指定src/step_db.cpp存在，19222字节，SHA=`037cb6915a411454d8eb3e0c3eaecf1f172c7e53bea3fe6ea43426aea9a9ce7d`；全源码读取/哈希不声称逐行审计整个Meep。

人工重点读公开driver.cpp/run_case.py/CMakeLists.txt/任务cylindrical.py、README/pyproject/MANIFEST、两例problem.json/grading.json与MSH。解释性要求仍由三文档给出，工具源码不补物理。

## 两例全覆盖

两例均radius=2、half_height=1、radial_pml=axial_pml=1、resolution=30、source_amplitude=1；01的mode=-1，02的mode=+1。两份输入HDF5各恰4项：int64 face_ids=[11,17,23]、probe_ids=[7]，float64 probe_coordinates=[[1.0166666666666666,.016666666666666666]]，times=[0.]。坐标与DATA规定运算顺序逐位一致。

MSH4.1 ASCII已完整读取并通过实际read_mesh几何解析。四节点为1=(0,1,0)、2=(2,1,0)、3=(2,-1,0)、4=(0,-1,0)；三条type1线11=(1,2)、17=(2,3)、23=(3,4)；另有每节点唯一的4个允许type15 point元素，无额外线/面/体/节点。两例网格字节相同。faces选择的是3条线tag，没有把可选point元素并入输出轴。

完整读取两例input、output、reference全部6份HDF5，每项均[()]全量读取，无遗漏数值数组。输出/公开参考各恰7个key：face_ids、probe_ids、times、spectral_flux[1,3,1]、observed_dft[1,1,12]、time_step[1,1,1]、window_end[1,1,1]。全值/dtype/shape/有限性/属性/压缩保存在evidence.json.arrays；所有值有限，无额外属性/载荷，ID/times全部精确复制，不输出坐标或网格。

两例谱通量均[2.1071566794387158,2.535021335578007,2.1071566794387158]，dt=1/60、window_end=1080，符合N=64800与静态标签约定。复场12分量均完整读取，不能只看正负模式通量相等：例如01的Ephi=(.605542577897168,.16813737141911878)，02为其相反数；其他各分量全值已保留。每例output与公开reference文件摘要相同。这只表明公开材料自洽，不认证参考的真实离散求解数值。

公开适配器serialize输出两例分别为 `2 1 1 1 30 -1 1 50 10 80` 与 `2 1 1 1 30 1 1 50 10 80`，完整保留参数；adapt仅将真实flux/fields/dt/time转成规定shape。直接以已公开数组构造原生格式回放适配器，四个输出数组逐值完全一致，没有纠正、归一化或替代观测。

## 实际工具与变体

复现命令：在仓库根目录执行 `python runs/candidate-review/repair22-meep2338-exam/audit_public.py`。这是中性审阅脚本，不包含求解或修复；evidence.json.commands记录全部37次子进程调用。

主机Windows/Python3.11；PYTHONPATH仅指向公开包src，未安装editable包。未执行pip安装，info报告core_version=uninstalled，同时正确选中task.cylindrical-field-pml-repair及对应assembly。因此本轮是主机既有依赖下的工具验证，不是普通离线pip安装/锁定镜像证明。

两例各实际运行（S=01/02）：

```text
python -m caeoj info --input qbank/19-solver-repair/19.6-waves/cylindrical-field-pml-repair/samples/S/input/problem.json
python -m caeoj validate-input qbank/19-solver-repair/19.6-waves/cylindrical-field-pml-repair/samples/S/input/problem.json
python -m caeoj validate-output --input qbank/19-solver-repair/19.6-waves/cylindrical-field-pml-repair/samples/S/input/problem.json --output qbank/19-solver-repair/19.6-waves/cylindrical-field-pml-repair/samples/S/output/result.h5
python -m caeoj grade --input qbank/19-solver-repair/19.6-waves/cylindrical-field-pml-repair/samples/S/input/problem.json --output qbank/19-solver-repair/19.6-waves/cylindrical-field-pml-repair/samples/S/output/result.h5 --grading qbank/19-solver-repair/19.6-waves/cylindrical-field-pml-repair/samples/S/reference/grading.json
```

8条均退出0，valid=true、scope=task-contract，两次grade accepted/score=1。SDK真实load_problem/load_result、write_result再load_result，所有字段/身份/时间逐值完全相等。

消费反例：两例四个输出字段各自最后一个标量加100，共8次grade；另对01复场其余11标量和谱通量其余2面分别单独加100，共13次。**合计21个独立扰动均退出1/wrong_answer**，覆盖12个复场标量、3面通量及dt/window_end。包内grading逐quantity的pointwise容差与题面完全一致。

中性合法输入变体：负幅度-.25、翻转mode、resolution=40且按DATA重算probe坐标，均validate-input退出0。非法变体：radius=2.0、radius=true、mode=0，均退出1；浮点整数/布尔不能通过类型或模式声明检查。这些只验证契约接线，没有求解变体。

## 真实执行缺口

两次实际运行公开run_case.py，均因Windows主机缺 `/opt/meep-repair-build/bin/cylindrical-driver` 而FileNotFoundError/WinError2退出1，未生成真实结果。未将该主机限制冒称锁定镜像故障或考生数值错误。

真实原件健康检查、候选文件重新编译/重链、离线普通pip安装、真实Meep FDTD、1800秒每例/300秒编译/30秒评分及4GiB资源均未实测。没有审计隐藏数据/私有方法验收，没有证明参考数值精度。未发现确认的公开材料障碍；可选公开覆盖观察为样例只在R2/Z1/PML1/res30检查正负模式，其他合法几何/分辨率未实际求解。本报告结论仅适用于上述冻结SHA。
