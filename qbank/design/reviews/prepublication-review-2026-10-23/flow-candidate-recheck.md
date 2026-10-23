# 流动43题修订窄复核

结论：43/43题FC-01均已解决。新版instruction在“公开格式样例”中明确指出samples/01/output/result.h5为随机格式示例、不是数值解、不保证物理约束，不得用作正确答案、误差参考或本地数值判分依据。允许用于数组、IDs与时间轴读写，与此前全部样例结构检查通过一致。

复核范围严格为 flow-revised-whitelist.json 所列公开三文件与样例。原审阅全文和38题数值反例保留；本轮按原SHA复用未变文件的既有审阅，不读实现、隐藏参考、作者材料，不重做求解或评测。随机生成的实现来源不在复核范围；考生现已能直接从公开题面确定样例角色，无须猜测生成机制。

## 修改边界

逐文件重新计算并核对白名单SHA：301/301匹配；唯一文本改动是43份instruction末尾附加相同的样例说明。43份DATA、43份CONTRACT与172份实际sample文件共258份均与原版SHA相同。原instruction全文（按行含义）均保留，新增段落之外无删除、改写。

因此没有引入模型、材料、边界、初态、采样、输出契约、评分容差、正式算例通过条件或运行资源变化。对格式样例排除数值验收是明确对象角色，不是对正式提交放松物理/数值要求；原来的三文件规则与新增说明没有冲突。

原报告中的负密度/温度/水深、负相含率/方差、非正定构象等反例仍对应同一输出字节。它们现在与公开标注的格式载荷身份相容，不能再被当作正式答案错误。本轮不证明隐藏参考正确，也不证明资源预算可达；原FV-01证据边界继续保留，可选数值小样例建议FS-01继续有效。

## 逐题最终文件身份

下表SHA均为本轮实读文件。每题结论：FC-01已解决；说明之外无语义/评分改动；未变sample/CONTRACT身份复用原审阅。完整301份文件身份保存在 flow-candidate-recheck.json。

|任务|最终instruction SHA256|最终DATA SHA256|格式说明行号|结论|
|---|---|---|---|---|
|`newtonian-incompressible-steady-2d`|`92eeaa60d0307dbc6b824c0db5deeea1ca7f7689c33fcf99c74de75159a543da`|`d2c61547d59c411f1a6b3f45879003a216fc2819313f69d2f4d3de2e3cd5b4af`|77|通过，FC-01关闭|
|`newtonian-incompressible-steady-3d`|`6c051d3a2083684c184bbf151bc20daeb31a89b928ec2ad1ab383dc1793a3483`|`4799e680f96389d731f8dc0c39ebc3afaee25a587c619420f3f47961fe43a40c`|77|通过，FC-01关闭|
|`newtonian-incompressible-transient-2d`|`e55be589b016dc6052fd52396b9e2d76da0d8790e6e8a49e536c9f5d8217b16c`|`38e607ad69c3c88a1bbb1dffc4da0c0e897b586bb626eedfef6af02516d5d33b`|77|通过，FC-01关闭|
|`newtonian-incompressible-transient-3d`|`8bdc74e1c1fa2d337031a22c4c7032d40b6e8e0d94f6007c07ff740b9f0d9869`|`4ae49ac05fd59cbc530bd956d762f74686fd3756e1d2f42766ff6083046bd63c`|77|通过，FC-01关闭|
|`generalized-newtonian-incompressible-steady-2d`|`a2ac65ed56a95b4f2a58756a013b287e6b1ba8efcd5dcb452cd8ccde2e2c8073`|`58de1aa48b521fa6b612d956c2305094a5e9c5ec258f0f028621f31c404444cf`|77|通过，FC-01关闭|
|`generalized-newtonian-incompressible-transient-2d`|`bb899808d403aa5152ae393ca8d6e73a1e86e9dc8ec7fd0bdc79d628ee8d55c1`|`c18d56594243f259fcba9e02f5d2a44a22d94e40105480f4727833442fa661a3`|77|通过，FC-01关闭|
|`generalized-newtonian-incompressible-steady-3d`|`f50f4d06d2dc574c3a80fdab0d6d776573ec5d54f315ef477ddded9e7dd4c0e5`|`be035ffea07417cb3588415dcf56dc238c60223baa1368991d84ca5d77f6c335`|77|通过，FC-01关闭|
|`generalized-newtonian-incompressible-transient-3d`|`777daf50648aa22ca94aaa4bf209d9acffe173da3de76600d31c423aa3908d58`|`eae351d6e15953b36235f72917b88dd5b7b8e9725a32dacbe17e7c9c52108cdb`|77|通过，FC-01关闭|
|`newtonian-isothermal-compressible-steady-2d`|`66e19866b6e9c4a19c4b5c724b9ee9154176940b150e5688289a3fc543e8a4fc`|`d0c29d8198bafe76bfedeedefd5592d50cb2f273f511217ed8c489722ce375c8`|77|通过，FC-01关闭|
|`newtonian-isothermal-compressible-transient-2d`|`a15e96d9076198eea998926ba6936b9655303491149e9c13e467a282fb929c7d`|`b7d916325ae0d658ba77e5e956d4d27c0a68f1a8d7d376c9fe9048c1ddf1b033`|77|通过，FC-01关闭|
|`newtonian-isothermal-compressible-steady-3d`|`a56eae55c4d924879b45d1b2e763f1c6e1eba1380be07ac24833e3eb4874018a`|`b4202902c19b2611bdcbb66427d2727bdf4d010b6287f4aa16e6b9e1263f1682`|77|通过，FC-01关闭|
|`newtonian-isothermal-compressible-transient-3d`|`4021865346123da8545b4791d11c66ae83e49baa8314fa3a012723808dfc3486`|`b2d0a75588516422b964f406a8e4d57dde54a8f0f3465b97308334b50634fe5a`|77|通过，FC-01关闭|
|`newtonian-lowmach-steady-2d`|`da7ab0e6839358c6f9535decefaeaef926e0f5536f829ef8b3ff6f829410066c`|`6c850e0bd359652d0c424e7cdbdfd60f372d5c34fb83116e6f0bcb43b61664e4`|41|通过，FC-01关闭|
|`newtonian-lowmach-transient-2d`|`c9e1b74c0de789aa9aa9350d5cfc492e01a044e960d6505c3637fa370de4e72c`|`33dce098be1fdfff16c5adb3a2e32b97929ce4e4b81a7a25544ee0974a05fabb`|41|通过，FC-01关闭|
|`newtonian-lowmach-steady-3d`|`4b316597e312379ecd5fec93dea47f16cf2ff2908efbe10343a9ec1d0c534257`|`32ba3af50b06a3f388febfac8ece54dc405647edf05b62fe668732d57c6b0c94`|41|通过，FC-01关闭|
|`newtonian-lowmach-transient-3d`|`bfe71f04a8ae4b715c4edad3c8160045c69034682f120dd1116b4a9ca3e19a93`|`c7d05bedfbed0331294715d063952563f08513f18e5ffe4571ae63d9cc10cd4d`|41|通过，FC-01关闭|
|`inviscid-compressible-steady-2d`|`df717ace37e8d9703da3bc78ad6e3b4bb8d4c0367a77eac993ec79089f336532`|`b2397173bb1bf60c77a9971b6ff5b9930fde219f15202b32cc3f059695dbcc3e`|42|通过，FC-01关闭|
|`inviscid-compressible-transient-2d`|`8a86e90f51c638f9fd571cc8808425e48fee82fe643e7a3e32d9766d81de8d04`|`48846766c7cecd0c68f9e792299fccb81163f8b3b220a75fd40785d977995df1`|42|通过，FC-01关闭|
|`inviscid-compressible-steady-3d`|`19e23fcf5b16fcdbe231410148efb0ef3241073ae8717f96bc35da3ed0bb66d2`|`6704a3495df823a044cc6ad9028e162be155954fdd5293c7589a9e71936dfb4f`|42|通过，FC-01关闭|
|`inviscid-compressible-transient-3d`|`b1cc83d747ff0561369600d70f882b904c18b3bf5b3c679c546b8da3a526e11a`|`a60b50ae3021ed149242344d7b2e37b390a6e49cf0b5c82a876ace93a546ed6a`|42|通过，FC-01关闭|
|`newtonian-compressible-transient-2d`|`6e6b681cf4a14ab2c5288df23c50d69062cfa572c48c6003ef4684cb7c20bc23`|`de13a3baa463b92d41b916bcd943bf993b8413d50115db2aaff595bbcaf436f2`|42|通过，FC-01关闭|
|`newtonian-compressible-transient-3d`|`0f97a253cfc8f7c68efd49d01a38ca4b7e0ac091997254dc382fad5ca5309c76`|`5e2e99c2c1099aff9531650aa507c29c6a31806e1ed8306f79a9017dbb25df10`|42|通过，FC-01关闭|
|`rans-steady-2d`|`ad3157eddda8d0473abfb58c17d012bb0e1df9cfe561e29a27396ca3307f075f`|`0f7e4775ce2cc21d93f5e3655d6e0a91ff636b2c7aceddd8eb98d28b918fefe5`|40|通过，FC-01关闭|
|`rans-steady-3d`|`e2bddeb6f34fe1e3028ddfe0ddfe436c79d556efe094cdc7a3274ae82a241529`|`ec854f705faabc49ce325de5382d8010da1fc311e110f40f2ca6cbf6fea66958`|40|通过，FC-01关闭|
|`urans-transient-3d`|`7cf91f9286ad058e249a24d9db95ac2f72b06f118d3e705a75b579668b3537de`|`951dbb548e0f694584c29244ddc448ed72785fa19e7f7b63e3d23df8517122e5`|40|通过，FC-01关闭|
|`resolved-statistics-3d`|`56d6932fab3c1bbcaf7b2724d4c4240d77d8ba1f00c238f6656da81275810b4f`|`7fb8d82a1a172e86b980ac33b6301233aee2e27e1ba44ea316af866d072ffcad`|41|通过，FC-01关闭|
|`isothermal-rans-3d`|`4767ac1ced610b4674fc52e2b0429eb04d4efe595ee8424ebbbb66511cf5cbc6`|`bc2d523f52ad74a2d36cd237f681e8f6e0057a169f09142ec9d759707dbac2e3`|41|通过，FC-01关闭|
|`thermal-rans-3d`|`b18ee8fe02d545488f3a43ee380a39ac9d13ae3e285364136566d2ec3437db7f`|`5d947561edfc9bca8d1e923b783a6baf1080bade5b6c154a993e296627edc2bb`|41|通过，FC-01关闭|
|`thermal-urans-3d`|`cd8c148ded6eb9a221e0de3e2d964fe8966f0ee8cf3b4d8c3115f0eaa46cdd51`|`b5a605aa9e917a65f631d101ca8856fcfaefd55d301437ca230e12902ae2fe14`|41|通过，FC-01关闭|
|`thermal-statistics-3d`|`1ba73c91815fb66587fce6bd64d853372acb93370c585ce072f98e38893e99b3`|`13639f2a0d52a813fd759968d8c7c5de32274d13cb125914c000ffa748371878`|44|通过，FC-01关闭|
|`immiscible-interface-2d`|`c1d0b8d1bf0277e96d8b21da6e9fe2801d77f7705958b19227dd08c4ba5b4d3b`|`42dfaf9cbd7a6d641c5924773b31c1f37fe8451db7005356911d780177135743`|53|通过，FC-01关闭|
|`immiscible-interface-3d`|`c237effd1632518a2e8b286300e47455c8438280c87e2c03e795e05eb2df25d8`|`5fb05829f97f4849dad51d0c6cb458fda188d8ec408d4b6b7dec3d6ffba42ae2`|53|通过，FC-01关闭|
|`gas-film`|`f7a54f3788efcfcd9a1ac7277d856d067c64b466fbfdf0ab422f3e229427a2cf`|`b10037e6696aa34b4922d2039082b5225fe0dd0a76e2c2bb7afcc80fca45eeb6`|32|通过，FC-01关闭|
|`fully-wet-steady`|`ff29f2751e1189fb012637fbb78ef256ae6858a86b56c22deee0caba71effabc`|`f2f9066585d78b247c579367df46e86b50a90887cd580e3ac658f75ae9d353f5`|32|通过，FC-01关闭|
|`fully-wet-transient`|`9f470d2b5eed69a7677a5ce35217924cd3c0f82d79562ed58d29b0900ee0d388`|`f5adf3dcb4a95af4da1b64bf2c33f2fd45cacd52e14288a35f325d61ff4d60b5`|32|通过，FC-01关闭|
|`wetting-drying`|`0e4cd1e63f331d9c42076ca4879ca60e7846828c495341f596e8520ebec4962e`|`d4d660cdf24ff1ca31065328a82454f03bdfe71e39ad424d3182d20575416215`|32|通过，FC-01关闭|
|`transition-gas`|`8b16194b13d5e4f3dd60e41ee49581ae5d1e76b3ee8496bcca9e6a68ee3cfc9d`|`366a48ff0448a8b5276e06a9a811bc5a993d560dbe3313d8c98b387be7cabbcf`|34|通过，FC-01关闭|
|`free-molecular`|`1c7ca972fb164729e16b9fe713de31e4c1ba8b725260530e6bd60ef4b7b5c105`|`da7f2ccbb8866eed1a36024de2287f4b9b3fa4511b60fd3180717bbdef9ed7c4`|34|通过，FC-01关闭|
|`viscoelastic-steady`|`740b6fdee953b07ebb7b0d5fba2773130c7a4faebdc0ee140b207d50c92f8913`|`dda9c11e0cb8a3d78fec179f939f1d43d2056dad8ba358098f263aedb145fa01`|33|通过，FC-01关闭|
|`viscoelastic-transient`|`2b4d05abc1d59e887997ce03eb0fd29e817a2dbbb7d4be53218399004109332f`|`1224eb8719587deab16aae844a78ec21d69b502f24f9e1389ae5cc34c0f1941b`|33|通过，FC-01关闭|
|`newtonian-compressible-steady-2d`|`16489d43170d6338a2dbf2adba5e63f1b86a087e8c1d3f4565adfea71f61a6c4`|`3dd8842678116a1c88fcdda89eee9b3cdc1313aa6f462b85b6ddfdc7e4604856`|42|通过，FC-01关闭|
|`newtonian-compressible-steady-3d`|`c40cfe36a20cdf32280b53a4fc2ebbc2532f857acc61681fa4ebfc02cd1f4db4`|`31ef87e3792e60b09b36de9f2d4e65b1fc8afc418e387c4154cf2c194e8854d0`|42|通过，FC-01关闭|
|`compressible-thermal-rans-3d`|`1721d711618e8326583fe7afc00d80c64ac3d314aea81b8af8ce637a2f8dcd9d`|`304ffc1be000c7dd3aa23442eb7659e3d7bbd8e28f92bdd3c6beee215bf2391a`|42|通过，FC-01关闭|
