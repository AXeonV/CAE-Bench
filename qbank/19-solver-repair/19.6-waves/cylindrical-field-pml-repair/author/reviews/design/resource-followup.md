# Meep2338 资源范围有界复核

结论：原设计审阅中公开600s预算的资源缺口已关闭为1800s；不据此宣告正式数据、ZIP或后端就绪。原report.md与12e236版scope结论完整保留。

新scope SHA256 `cdc846af6339ea1fd3e2efb3ae1541a7d960bf52e466d850cd5c34e200040090`，独立读取本次资源追加段及正式instruction/judge-config：单例1800s、评分30s，编译候选/原件各300s；原物理范围保留。外层预算设计1000+8×(1800+30+5)=15680s算术一致；尚非正式prepared预算实际运行验收。

实际读取并两层解析 `runs/authoring/repair-22/meep-2338-resource-corner.json` 的原生stdout与外层容器记录：固定producer `sha256:7a0236142085710589f832d009cd57bb1f8ceaa3e2dd974e9f4a3a76a044c396`，最大合法corner R3/Z2、r/z PML各2、res40、m−1；payload `3 2 2 2 40 -1 1 50 10 80`，原生time1080、dt.0125即86400步，名义200×320格。原生1082.97305814s、host总1085.875s，exit0、无stderr；实际UID1000、cgroup cpu.max=400000/100000、memory.max=4294967296、memory.peak=31453184 bytes。真实无作者trace生产路径，未由4CPU名义配额推断提速。该次最大corner实际小于1800s，约717s余量；单次测量不能证明任意主机负载下固定耗时。

旧阶段实际841.187s超过600s的证据保留；当前结论采用本次最大corner真实完成。原作者完整trace有额外采样开销，不混为正式无trace执行资源。证据副本及独立解析见resource-followup.json。未重跑原生计算；没有将本资源有界复核冒称8正式例全数据、HF、Oracle、公开包安装或后端通过。
