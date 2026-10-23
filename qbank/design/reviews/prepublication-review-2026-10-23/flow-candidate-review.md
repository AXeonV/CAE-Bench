# RC2 流动43题独立考生审阅（原始材料）

审阅模式：exam-materials。仅使用 flow-whitelist.json 列明的 RC2 公开快照，未读作者实现、维护报告、隐藏 cases/reference、设计材料或外部物理说明；未写 solver、未运行模型评测、未重做参考。全部43题的 instruction、DATA 和 CONTRACT 已读；三文件完全相同的行按精确文本去重审阅，各份全文字节另逐项验 SHA。所有实际样例表示分支均检查，既覆盖实际节点/单元/独立点/aggregate，也覆盖实际constant/linear、uniform/piecewise_constant/piecewise_linear及MSH三角形/四边形/四面体/六面体。

## 结论

公开任务的模型责任、输入场、条件、重建、压力规范、输出和评分/资源总体可由三文件确定；没有因自选建模/闭合而要求固定算法或额外方程。确认一项跨43题的公开样例说明缺陷 FC-01。43份样例结构检查均通过，但38份存在无需求解器即可直接证明的数值物理反例。其余5份仅列为数值待核实，不以数值外观推断错误。

### FC-01 [P1] 样例输出缺少“仅格式/非物理解”的公开角色说明

位置：43题 instruction/DATA 的输入输出与评价说明，以及各题 samples/01/output/result.h5。三文件没有告知这个输出是否仅作格式演示；题面又要求全部输出满足所述物理量语义，不能靠不可见的维护配置给随机/格式载荷补角色。下表38个直接反例中的负密度、负绝对温度、负水深、负alpha、负方差、非正定构象都不能用同一题面要求解释为数值答案；完整索引、实体ID、物理时刻及SHA见机器summary及 numerical-counterexamples.json。

反例：二维双相 /alpha[0,1011,0] = -0.9999923624306764（体积分数应在[0,1]）；全湿浅水稳态 /water_volume = -0.927588（总体积须正）；Oldroyd稳态 /conformation[0,311,1,1] = -0.9989588350528567（SPD对角必正）。格式合法显然不能推导数值有效。

影响：考生可能将输出当作可检验答案，合理的物理解反而与所谓样例差得很远，无法判断是实现错误还是数据角色问题。最小建议：若有意作格式示范，在考生三文件可见处明确“仅格式、非数值答案、不可用于正确性判分”；若需要数值样例，则替换为验证过的解。不要把随机数简单调整成正数冒充物理解。

## 待核实与可选建议

- FV-01（证据边界，非已确认缺陷）：全部43题精度与资源预算的真实可达性仍需独立基准执行证据。本次没有求解器，不将结构通过或题面保证当作数值验收。
- FV-02（5题）：两道常黏度不可压缩瞬态、两道定常不可压缩RANS与URANS的输出也均在约[-1,1]。本次没有把这种外观单独定为数值错误，也不以小的平均压力漂移替代真实解验证。共享FC-01依然适用。
- FS-01（可选）：补少量数值可信的公开小例以核对单位、符号、统计及张量，不要求穷举所有分支。

## 43题逐题覆盖

表中“结构通过”只指独立中性检查；“反例”明确禁止被解释成数值验收。所有题均覆盖任务/物理/条件/采样轴/输出/评分/资源。

|题号/任务|实际样例审阅重点|样例状态与直接证据|
|---|---|---|
|1. `newtonian-incompressible-steady-2d`|常密度、点压力规范、多源相加；points/node/element/mean与边界sum均有实际样例。|结构通过；物理反例：`/density` `[0, 2, 0]` = -0.8639537012696845；密度严格正（部分题为给定正常数）。|
|2. `newtonian-incompressible-steady-3d`|绝对压力、节点分片线性pressure_outlet、多个加速度、边界traction与sum。|结构通过；物理反例：`/answer_density` `[0, 4, 0]` = -0.27542771474371963；密度严格正（部分题为给定正常数）。|
|3. `newtonian-incompressible-transient-2d`|物理零初速；history线性边界与requested四时刻分离；完整域单元平均。|结构通过；数值待核实FV-02；样例角色未明FC-01。|
|4. `newtonian-incompressible-transient-3d`|完整3D六面体；分割顶壁线性历史；物理初速与输出时刻分离。|结构通过；数值待核实FV-02；样例角色未明FC-01。|
|5. `generalized-newtonian-incompressible-steady-2d`|带截断幂律、周期平移配对、体加速度；单元平均与外边界sum。|结构通过；物理反例：`/density` `[0, 1065, 0]` = -0.9991675133359734；密度严格正（部分题为给定正常数）。|
|6. `generalized-newtonian-incompressible-transient-2d`|带截断幂律、初速度、分段线性源历史与独立requested；周期无压差。|结构通过；物理反例：`/density` `[3, 338, 0]` = -0.9999481322613506；密度严格正（部分题为给定正常数）。|
|7. `generalized-newtonian-incompressible-steady-3d`|3D流率入口；rate uniform及shape节点piecewise_linear；外部储槽牵引。|结构通过；物理反例：`/mass_flow / volume_flow` `` = [-0.4077273539700037, -0.45417561352334057]；density=1 kg/m3，完整相同区域与时间的mass_flow=volume_flow（SI单位）；两值相差约0.046449。。|
|8. `generalized-newtonian-incompressible-transient-3d`|3D幂律瞬态、周期平移、线性源历史；多类强度与sum。|结构通过；物理反例：`/density` `[3, 8293, 0]` = -0.9999416627227529；密度严格正（部分题为给定正常数）。|
|9. `newtonian-isothermal-compressible-steady-2d`|等温理想气体；mean_density固定库存；闭池顶壁运动；绝对压力。|结构通过；物理反例：`/pressure` `[0, 911, 0]` = -0.9993165248372862；绝对静压严格正。|
|10. `newtonian-isothermal-compressible-transient-2d`|等温初密度决定压力；time_interval与多帧壁速；输出非初态。|结构通过；物理反例：`/pressure` `[1, 82, 0]` = -0.9997733538693683；绝对静压严格正。|
|11. `newtonian-isothermal-compressible-steady-3d`|3D等温理想气体；mean_density与壁运动；无隐含pressure_gauge。|结构通过；物理反例：`/pressure` `[0, 364, 0]` = -0.9998524219416542；绝对静压严格正。|
|12. `newtonian-isothermal-compressible-transient-3d`|3D初速度/密度及变动壁面历史；绝对压力与瞬时单元平均。|结构通过；物理反例：`/pressure` `[3, 7157, 0]` = -0.9999467529986921；绝对静压严格正。|
|13. `newtonian-lowmach-steady-2d`|Boussinesq/温度幂律；封闭静壁、两壁温和向外热通量；域均值压力。|结构通过；物理反例：`/temperature` `[0, 267, 0]` = -0.992809141305323；绝对温度为正且本例至少280 K。|
|14. `newtonian-lowmach-transient-2d`|低马赫初速度/温度；条件time linear；输出四个物理时刻。|结构通过；物理反例：`/temperature` `[0, 272, 0]` = -0.9981791526593176；绝对温度为正且本例至少280 K。|
|15. `newtonian-lowmach-steady-3d`|完整3D低马赫；独立机械/热边界分区；全部体单元平均。|结构通过；物理反例：`/temperature` `[0, 700, 0]` = -0.9999495810005616；绝对温度为正且本例至少280 K。|
|16. `newtonian-lowmach-transient-3d`|3D低马赫初态、线性热边界；常体密度与域均值压力。|结构通过；物理反例：`/temperature` `[0, 11955, 0]` = -0.9999901212169555；绝对温度为正且本例至少280 K。|
|17. `inviscid-compressible-steady-2d`|平滑等熵静水平衡；质量库存、熵常数与体加速度；明确u=0。|结构通过；物理反例：`/density` `[0, 330, 0]` = -0.9925635415666472；密度严格正（部分题为给定正常数）。|
|18. `inviscid-compressible-transient-2d`|无黏瞬态理想气体；独立初密度/温度；滑移绝热壁；允许熵解。|结构通过；物理反例：`/density` `[1, 489, 0]` = -0.9982024315706324；密度严格正（部分题为给定正常数）。|
|19. `inviscid-compressible-steady-3d`|3D等熵静水平衡；源加速度、库存与熵常数共同定压。|结构通过；物理反例：`/density` `[0, 11230, 0]` = -0.999988364252957；密度严格正（部分题为给定正常数）。|
|20. `inviscid-compressible-transient-3d`|3D无黏瞬态六面体；初态与输出非均匀时刻；滑移绝热外边界。|结构通过；物理反例：`/density` `[3, 54, 0]` = -0.9996091308736503；密度严格正（部分题为给定正常数）。|
|21. `newtonian-compressible-transient-2d`|可压缩气体初态；独立体黏度、压缩功/耗散；热边界历史。|结构通过；物理反例：`/density` `[1, 1026, 0]` = -0.9995032141136033；密度严格正（部分题为给定正常数）。|
|22. `newtonian-compressible-transient-3d`|3D可压缩瞬态；初密度/速度/温度、机械/热边界；普通单元平均。|结构通过；物理反例：`/density` `[3, 3944, 0]` = -0.9999983095587475；密度严格正（部分题为给定正常数）。|
|23. `rans-steady-2d`|稳态RANS；闭合及近壁由考生选择；平均速度与域规范压力。|结构通过；数值待核实FV-02；样例角色未明FC-01。|
|24. `rans-steady-3d`|3D稳态RANS；全封闭移动壁；自选闭合，模型误差计入评价。|结构通过；数值待核实FV-02；样例角色未明FC-01。|
|25. `urans-transient-3d`|URANS标准化初态k/长度尺度/各向同性应力；不要求精确ensemble。|结构通过；数值待核实FV-02；样例角色未明FC-01。|
|26. `resolved-statistics-3d`|DNS/LES责任、完整瞬时初态；21帧等权统计，先空间平均再中央矩。|结构通过；物理反例：`/velocity_covariance` `[0, 4382, 0, 0]` = -0.9999557560855126；协方差矩阵对角方差必须非负，并且对称半正定。|
|27. `isothermal-rans-3d`|固定温度气体RANS；Favre速度、Reynolds压力/密度；库存。|结构通过；物理反例：`/density` `[0, 5744, 0]` = -0.9999003502141872；密度严格正（部分题为给定正常数）。|
|28. `thermal-rans-3d`|低速热RANS；Boussinesq与热闭合自选；静壁温度驱动。|结构通过；物理反例：`/temperature` `[0, 2379, 0]` = -0.999554462039492；绝对温度为正且本例至少280 K。|
|29. `thermal-urans-3d`|热URANS标准化二阶初态、k与长度尺度；多个热条件实际分支。|结构通过；物理反例：`/temperature` `[1, 6092, 0]` = -0.9999807955705464；绝对温度为正且本例至少280 K。|
|30. `thermal-statistics-3d`|尺度解析热统计；21帧离散均值/方差/协方差；热通量不含rho cp。|结构通过；物理反例：`/velocity_covariance` `[0, 8553, 2, 2]` = -0.9999760202042947；协方差矩阵对角方差必须非负，并且对称半正定。|
|31. `immiscible-interface-2d`|双相均求动量；纯0/1单元初alpha唯一界面；无表面张力；输出晚于起点。|结构通过；物理反例：`/alpha` `[0, 1011, 0]` = -0.9999923624306764；相体积分数必须0≤alpha≤1。|
|32. `immiscible-interface-3d`|完整3D双相；纯相单元初态、共同体加速度、闭壁；绝对压力均值规范。|结构通过；物理反例：`/alpha` `[0, 7009, 0]` = -0.9998641566687085；相体积分数必须0≤alpha≤1。|
|33. `gas-film`|理想气体薄膜；节点线性gap及壁速、边界常值压力；点通量/整体载荷。|结构通过；物理反例：`/pressure` `[2, 166, 0]` = -0.9994332669767414；绝对静压严格正。|
|34. `fully-wet-steady`|全湿定常浅水；储槽Riemann只注入入射特征；点值与面积水量。|结构通过；物理反例：`/depth` `[0, 61, 0]` = -0.9999354367698783；水深必须非负，全湿题严格正。|
|35. `fully-wet-transient`|全湿瞬态；节点分片线性初态、固定床、全墙；深度/速度点值与总体积。|结构通过；物理反例：`/depth` `[3, 23, 0]` = -0.9955531910053108；水深必须非负，全湿题严格正。|
|36. `wetting-drying`|干湿守恒熵解；h=0速度为0、无物理干阈值；点采样避前沿多值。|结构通过；物理反例：`/depth` `[2, 266, 0]` = -0.9997372200200179；水深必须非负，全湿题严格正。|
|37. `transition-gas`|硬球Boltzmann显式碰撞；壁混合反射和储槽；内部节点与壁面平均观测。|结构通过；物理反例：`/density` `[0, 841, 0]` = -0.998185574545728；密度严格正（部分题为给定正常数）。|
|38. `free-molecular`|无碰撞、允许多次反射；储槽可达排除任意库存；墙热/动量通量。|结构通过；物理反例：`/density` `[0, 556, 0]` = -0.9988522861066695；密度严格正（部分题为给定正常数）。|
|39. `viscoelastic-steady`|定常Oldroyd-B；平面块Azz=1；无扩散；内部节点和避角边界平均。|结构通过；物理反例：`/conformation` `[0, 311, 1, 1]` = -0.9989588350528567；构象必须对称正定，对角项严格正。|
|40. `viscoelastic-transient`|Oldroyd-B物理初A/速度；线性壁速历史；全张量、压力规范。|结构通过；物理反例：`/conformation` `[2, 27, 0, 0]` = -0.9997983766353487；构象必须对称正定，对角项严格正。|
|41. `newtonian-compressible-steady-2d`|定常可压缩传热；库存与热壁确定绝对压力；体黏度及耗散。|结构通过；物理反例：`/density` `[0, 133, 0]` = -0.9944184672164564；密度严格正（部分题为给定正常数）。|
|42. `newtonian-compressible-steady-3d`|3D定常可压缩传热；非零体热源实际分支、机械/热分区；平均输出。|结构通过；物理反例：`/density` `[0, 1093, 0]` = -0.9996965434080907；密度严格正（部分题为给定正常数）。|
|43. `compressible-thermal-rans-3d`|可压缩热RANS；Favre速度/温度与Reynolds压力/密度；闭合自选。|结构通过；物理反例：`/density` `[0, 11674, 0]` = -0.9996918456698001；密度严格正（部分题为给定正常数）。|

## 文件身份与审阅证据

以下为每题三文件及样例输出SHA256；完整7份白名单文件的SHA、字节数、实际key/shape/轴/分支记录在 flow-candidate-summary.json。全部301个文件SHA匹配。CONTRACT 43份内容相同，SHA256均为 `130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063`。

|任务|instruction SHA256|DATA SHA256|sample result SHA256|
|---|---|---|---|
|`newtonian-incompressible-steady-2d`|`c03dfaa4b531272fb99cf69803c60bae7f4f65d12b30a9bbe21d3fbd2ad6311f`|`d2c61547d59c411f1a6b3f45879003a216fc2819313f69d2f4d3de2e3cd5b4af`|`1ef46f7f6f42ce49b4185b2d506f02dc9be1d9bff93195353d84a13cdd11a501`|
|`newtonian-incompressible-steady-3d`|`5d564b09fb2f0748b50ebaea7bf5b4819bf269b7ae0371e9dbb63fcc7e32c26d`|`4799e680f96389d731f8dc0c39ebc3afaee25a587c619420f3f47961fe43a40c`|`89059c62af97bcffa408ac953b3147580325dc53e8977a5f230e28e418a56a02`|
|`newtonian-incompressible-transient-2d`|`272d5c9de48ceccb089583a8dcdb79bab2fd1cf903491207a664f1f5e4ea9eb0`|`38e607ad69c3c88a1bbb1dffc4da0c0e897b586bb626eedfef6af02516d5d33b`|`d248a6ffc7608679bcaa610cdd6e1b859ddba18d0f310ca008a7711e086f3297`|
|`newtonian-incompressible-transient-3d`|`bd30dc545d90d7c450cb526ce178e2118e2c59492c97698cacc0b2a02fc5072e`|`4ae49ac05fd59cbc530bd956d762f74686fd3756e1d2f42766ff6083046bd63c`|`bb83102216a90d9a85011753c2503793ea7593a6fd47a732ca8804f928e72dae`|
|`generalized-newtonian-incompressible-steady-2d`|`4afa3714b5ff683a3e2642994dd230d6fb6681842bfb601f3b31e5403301c7f5`|`58de1aa48b521fa6b612d956c2305094a5e9c5ec258f0f028621f31c404444cf`|`fddd97d28ba6a5a8289797c6c7ebf992ea2811c0addade13338063551156bf83`|
|`generalized-newtonian-incompressible-transient-2d`|`429cde765d93b51c1c85cdf785c3155e1038c7d1156332a1cc9b0040037b8bc4`|`c18d56594243f259fcba9e02f5d2a44a22d94e40105480f4727833442fa661a3`|`fd7165538df2ec2ac875950b9ccf0e7cd4c6ee69f3e9f1cbf1881f547291dda3`|
|`generalized-newtonian-incompressible-steady-3d`|`d09bc0b9df916c73cfad8801ded10e50b0d10187cf549d4c0afb152427f5a676`|`be035ffea07417cb3588415dcf56dc238c60223baa1368991d84ca5d77f6c335`|`0ec4f9ae2a79d16a7a002b0ef2f9fea16f124e3f39082454c9af3cc32b3f0e34`|
|`generalized-newtonian-incompressible-transient-3d`|`fbd6a19f95fe2d0ab1eff8076cabbc5dadbd4930a9390cb223e96652f58b5fd2`|`eae351d6e15953b36235f72917b88dd5b7b8e9725a32dacbe17e7c9c52108cdb`|`71f12d9e95ddee8816f426ac99deef811a7eaacb130738b7482e81905fe9c96d`|
|`newtonian-isothermal-compressible-steady-2d`|`fe4ce637f7e2a1b93f8a49f88151af1a48f193d6d1fa8b2851b4ceb741e69eba`|`d0c29d8198bafe76bfedeedefd5592d50cb2f273f511217ed8c489722ce375c8`|`f218ec0a3edfe0ffc3c82c9dbbbf629c114db0376e48ef2c5459c6b5937c5363`|
|`newtonian-isothermal-compressible-transient-2d`|`78e4797e53a4324805b25efc7f118f43833eca3ffbea918169e4612c0ed25a69`|`b7d916325ae0d658ba77e5e956d4d27c0a68f1a8d7d376c9fe9048c1ddf1b033`|`fd11664ac3eba4501d125f6c9504e6f1bef7d9aceb2216a8826f97caff449717`|
|`newtonian-isothermal-compressible-steady-3d`|`77c4e9c60dd2cfe4797d92e85352927d8331ffbab177aa87c1fec895f8cf0199`|`b4202902c19b2611bdcbb66427d2727bdf4d010b6287f4aa16e6b9e1263f1682`|`decf384041dd06c2d315743c4fe00c71344238048608191dca78a4b276d6b4e2`|
|`newtonian-isothermal-compressible-transient-3d`|`33c5298bea4d4d7b449b98406fc34047dfdf0d29f89bf519c2626a24b96e6684`|`b2d0a75588516422b964f406a8e4d57dde54a8f0f3465b97308334b50634fe5a`|`c0ac8b34acbb06f9179513c9a46763464869011bdd2ef41556553fbab6c93bc8`|
|`newtonian-lowmach-steady-2d`|`ca43fc178d2420ed1ec9c7666bfec0900029af08f2bcdfe90dc51ce36dc22dc0`|`6c850e0bd359652d0c424e7cdbdfd60f372d5c34fb83116e6f0bcb43b61664e4`|`ed5a249e6ec7e5ab37689c21b4a3fe51e63acc7efd9bc6a4d35514b94c2bfec9`|
|`newtonian-lowmach-transient-2d`|`22024ce6aab1d8d4ad3cae74cf0ae7552d3b335245e95296457ccf98c980daa3`|`33dce098be1fdfff16c5adb3a2e32b97929ce4e4b81a7a25544ee0974a05fabb`|`8b429b44912b60f5ef75f7c2f89e0aac389e6581c20dff0a059c312669445cf0`|
|`newtonian-lowmach-steady-3d`|`d955ac3def3eef7320a943ddd9d9a85f19ed098a1569f3cb29da9491872f08bf`|`32ba3af50b06a3f388febfac8ece54dc405647edf05b62fe668732d57c6b0c94`|`0f6af49a3c0ceda8294ace80c0188ec87419151429c472d335602a46b9e9cf02`|
|`newtonian-lowmach-transient-3d`|`a4919d82340ee94e6acbcb1ca7f511476094fc53ecc49a136888825de3d830c7`|`c7d05bedfbed0331294715d063952563f08513f18e5ffe4571ae63d9cc10cd4d`|`1aae6d606ac81d5c3f3f0d762eacc42c10a41f71941c73ea15fae253f1492eec`|
|`inviscid-compressible-steady-2d`|`b2b11c00179e24962d863f7c4da52f639aca094a204ace461d08a62f62830a09`|`b2397173bb1bf60c77a9971b6ff5b9930fde219f15202b32cc3f059695dbcc3e`|`2faf264cc14ba954fa94030d898f3c5a8581e970998e0977657bed59839536fb`|
|`inviscid-compressible-transient-2d`|`fadb08c4bb66c88b3d188bfd07a33b1893da83c7eea321f200146b409631c1a8`|`48846766c7cecd0c68f9e792299fccb81163f8b3b220a75fd40785d977995df1`|`ec187e9eda99b52e29217b0e6db5f130a3c5bab5b135e2291947c4b8ecada2e2`|
|`inviscid-compressible-steady-3d`|`65434822b90e544b37dd5c3d177d6aeed59a97cae02a4508e0ee1bf10600bf76`|`6704a3495df823a044cc6ad9028e162be155954fdd5293c7589a9e71936dfb4f`|`dd042d1a1a76f651c0cd73f77cf0c354027ee4b2b09911ee45e8da7f8bf21773`|
|`inviscid-compressible-transient-3d`|`95510951dd3fcf10c30c8f84daa598097a0a195aedaa10f1d9f2e05419274cbc`|`a60b50ae3021ed149242344d7b2e37b390a6e49cf0b5c82a876ace93a546ed6a`|`f13c6a0ec35fe5b182cc6abccd6e5628ce2d86152087124fee4f38329bfd5abf`|
|`newtonian-compressible-transient-2d`|`41cacd0eb450b338c12979732ff0d6063d72fd212d70bd3f59d9c7fe855806f1`|`de13a3baa463b92d41b916bcd943bf993b8413d50115db2aaff595bbcaf436f2`|`01e04e96dc026843a42e029cf89c0f76d774eb2484414e816a14a7dd071c9a96`|
|`newtonian-compressible-transient-3d`|`cf87bcfd332b6c9e1b7f7bb194b4421279a86e9249ea92f7fc782ed54b3d46d2`|`5e2e99c2c1099aff9531650aa507c29c6a31806e1ed8306f79a9017dbb25df10`|`e523b18fe3969f97d5b7e7c4835ba5d552c06580549343ca7fe504818ded13cc`|
|`rans-steady-2d`|`653f37d614181970ff6c1ad56b998bf9d4dd0fee6ed5bfa57285af53ba9218d0`|`0f7e4775ce2cc21d93f5e3655d6e0a91ff636b2c7aceddd8eb98d28b918fefe5`|`5640b97c67bc802f1c55174b9744aeb6cd1512d6a95f22dcf330c96c6245b40d`|
|`rans-steady-3d`|`f31725f800c9547fc65b974c57747745d6d34e78a2547843017e76da22850bfc`|`ec854f705faabc49ce325de5382d8010da1fc311e110f40f2ca6cbf6fea66958`|`37375dcfe7a4935a4b7d7027cddd2cd6fd596c59c22cb7fe3224a4667785555d`|
|`urans-transient-3d`|`51fff839997d882389bfcd88db2ca456e67e5bea7586cfaf644c8a717643b207`|`951dbb548e0f694584c29244ddc448ed72785fa19e7f7b63e3d23df8517122e5`|`dae6ccea98c0a679c0247e3acbdf2ae7a865e33f2d722afdc43472a79c5616b3`|
|`resolved-statistics-3d`|`530ef358edf916a23c35dba76ceeac506e44811b3a897c95e650a3905b6ada52`|`7fb8d82a1a172e86b980ac33b6301233aee2e27e1ba44ea316af866d072ffcad`|`c4a9b8b0f3ed3ff6d27a8fd24cb0358a2a0bb4313b5e4814e7d9b22b301342a8`|
|`isothermal-rans-3d`|`556230efc0c49ca3c98d546e222e0919cd7183ccee7af73585032dabb7de72de`|`bc2d523f52ad74a2d36cd237f681e8f6e0057a169f09142ec9d759707dbac2e3`|`b0a03dd46a69fc022bf8ce8807ca12ae0dd8886da2896860e98ae5775db26cd8`|
|`thermal-rans-3d`|`337cc31917ba099279d4d24c83669e7438820f33f5fdd2b3a4724428690cfcc5`|`5d947561edfc9bca8d1e923b783a6baf1080bade5b6c154a993e296627edc2bb`|`577e647b8364da3a8a8242ed60a0c0ab0b2600f962541dafec8a1c7be0cd51e0`|
|`thermal-urans-3d`|`8c08c74f5941919972c4b8e2d0b2816906297ceb8806b94475c7bfd619be1358`|`b5a605aa9e917a65f631d101ca8856fcfaefd55d301437ca230e12902ae2fe14`|`25be3cd17497755283554f25afd1f3df5fad68b0525c62bc8bda1fa0b551d885`|
|`thermal-statistics-3d`|`c87b2ade1b26036a3d3bd5019617b54020e16af9a4fcd62f738a469548d2fe0d`|`13639f2a0d52a813fd759968d8c7c5de32274d13cb125914c000ffa748371878`|`10dcc749dd7d85887a75bebf1dc6b391d7b84e5b0d1321067dc4f678ac5bd51e`|
|`immiscible-interface-2d`|`32f23fa6b950328f2fd3bf7dc0eb96aa1228d1ff5d52c9d4da4bcb1d0de72d5e`|`42dfaf9cbd7a6d641c5924773b31c1f37fe8451db7005356911d780177135743`|`f965da93b2a317310bcb4314edb9581c207e023597b0cdddbc8ed670c6172980`|
|`immiscible-interface-3d`|`0ded5ec28b64bee3baf74a4e57de308f21ecbf2ef904d881b2b7744ec9e40425`|`5fb05829f97f4849dad51d0c6cb458fda188d8ec408d4b6b7dec3d6ffba42ae2`|`efc65a6a99a14869b18260dc3e7c64b34e35c7012bf753c79859c8271dc02688`|
|`gas-film`|`3a10c395efde340f0a8d717b8d1f64e660359a5732d94906fce2f00eaa87246b`|`b10037e6696aa34b4922d2039082b5225fe0dd0a76e2c2bb7afcc80fca45eeb6`|`cdb7e4ef1336fb8a4ab26f9a1ee686391815ec6fd1e26c804063cdadd288a74f`|
|`fully-wet-steady`|`69943aeff125f640af4dcb79a4a0048b2cfa611960e8e0f731624750e65f7eb3`|`f2f9066585d78b247c579367df46e86b50a90887cd580e3ac658f75ae9d353f5`|`5ca992948177f3dad6ba103cbcd8530dacc481589473aab6bf5d6af5381947b2`|
|`fully-wet-transient`|`5f41d4c6f06bac59af395f50d4a3693785a44c6eb4e92f17eacaa15233fcb80a`|`f5adf3dcb4a95af4da1b64bf2c33f2fd45cacd52e14288a35f325d61ff4d60b5`|`16d794bc80e3f5a7d22b4c87295ee2e8686ef47451a1b8b6c74dbc49fedf636b`|
|`wetting-drying`|`9d97f1b79764e48ca4979651b83c8174c5485971599b4a2b08d346f424d7a7f5`|`d4d660cdf24ff1ca31065328a82454f03bdfe71e39ad424d3182d20575416215`|`eaa0bfa74f4db92e3a8666a5ef3c02b044f67cbad425ed803e17149dbab15927`|
|`transition-gas`|`82d18dbf280a88f561f37c5e880c5bd605c644e166f710d6c9cdb2f6bbecb4c6`|`366a48ff0448a8b5276e06a9a811bc5a993d560dbe3313d8c98b387be7cabbcf`|`7b835f2e441100cd5a82aea5089161cff85122cffefcef3148fa98602a54dd98`|
|`free-molecular`|`a846956bdc496aa64ff90109f672051c68071d5b8e50a830a338ebef6e57ac6c`|`da7f2ccbb8866eed1a36024de2287f4b9b3fa4511b60fd3180717bbdef9ed7c4`|`81a36340bfc88590fd7e39546f656b2ec581613c27ceb3f2f07f4d2159be70fa`|
|`viscoelastic-steady`|`6f78e2e3cec07935b95ceaf43e69740aac75edfb42c9908f129a532d93c329fb`|`dda9c11e0cb8a3d78fec179f939f1d43d2056dad8ba358098f263aedb145fa01`|`16c095eff5aa8914c62797dedee8264c637b9131e9eb3953b2917c8a9e884406`|
|`viscoelastic-transient`|`c6620b88149f748fb9e3eea5f3a043b29c5c0fd7757c262ef320e0f568aa91e1`|`1224eb8719587deab16aae844a78ec21d69b502f24f9e1389ae5cc34c0f1941b`|`f07218ca0ba9bd26b2b28351779ed223b7f09d6e1c3ca6e84d7bef68d1c64931`|
|`newtonian-compressible-steady-2d`|`20eeda0d782a09358b9783921d8146905670f411fd96e7327829647cec36e411`|`3dd8842678116a1c88fcdda89eee9b3cdc1313aa6f462b85b6ddfdc7e4604856`|`95c2c35c706c186920bb8a1fc3fc74c1c86b310ae030dc2c91f459f0150600f1`|
|`newtonian-compressible-steady-3d`|`928c7f21e5589f2669ae4d6209af725d9da106a423dbc74cc11f63532e08498f`|`31ef87e3792e60b09b36de9f2d4e65b1fc8afc418e387c4154cf2c194e8854d0`|`a66a46334b240d00b77da8d08cb135e2e3362be24443b508f8c74f572b87f9f0`|
|`compressible-thermal-rans-3d`|`561ad0c58087ae830be659cdb8d9e8b61c23455a19334b80c507200c32740e8b`|`304ffc1be000c7dd3aa23442eb7659e3d7bbd8e28f92bdd3c6beee215bf2391a`|`1190a4ebf9c5bed3365531da4115214190138a7b867384d98bc9984987057f0c`|

中性检查包含：HDF5扁平结构、无属性、keys、dtype、shape、finite、支持轴原样复制、IDs/时刻严格递增、MSH4.1实体/Physical Group引用、真实外边界不重不漏、壁面法向速度、uniform一致性与线性空间采样的simplex条件。它不证明 PDE/守恒/压力/材料解正确。实际物理反例由直接读取公开output得到，完全不依赖隐藏答案。
