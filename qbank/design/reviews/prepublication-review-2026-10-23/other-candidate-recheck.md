# RC2 其他39题：修订公开材料窄复核

以 `other-revised-whitelist.json` 为唯一文件访问边界，复核 F1（格式样例身份）与 F2（运行入口）。原始 `other-candidate-review.md`、`other-candidate-summary.json` 保留不改，本报告不改写其原版发现。

**结论：F1涉及的35题全部解决；F2涉及的24题全部解决。未发现本次修订引入的新阻断问题。**

全部324个最终公开文件逐一重新计算SHA256，均与修订白名单一致。所有sample与CONTRACT的字节SHA与原审阅相同，复用原53例实际JSON/H5/MSH结构审阅。所有DATA字节不变。四道原无F1/F2题保留原语义；其中case-grading-test的instruction仅换行字节变化，规范化后与原文一致。

35题instruction均明确：样例仅展示输入与输出结构；output/result.h5为随机格式示例，不是数值解且不保证物理约束；不得用于正确答案、误差参考或本地数值判分。它们原有的数值反例仍成立，但现在已被公开、准确地限定为格式样例，不再造成“数值答案”的题意冲突。该说明由公开题面提供，不依赖维护侧不可见声明。

24个CFD题均增加同一明确提交契约：`python solve.py --input /path/to/problem.json --output /path/to/result.h5`；入口文件solve.py、每例独立启动、参数路径优先、输入引用相对problem.json目录解析、0退出、结果写到--output、日志不算答案、可调用其他语言程序，均已就地交代。

窄复核还将新增格式说明与CLI段落移除、恢复原“公开输入输出样例”措辞后重算SHA；全部更改均能匹配原instruction（允许换行规范化），未发生未说明的数学、字段、评分或资源变动。新增块共有三种：两样例格式声明×11题、一份样例格式声明×24题、CLI声明×24题。

## 逐题结论与最终statement SHA256

下表格式说明/CLI为最终instruction的一基行号。`—`表示原问题不适用。全部39份最终CONTRACT SHA256为 `130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063`。每题所有其他最终文件的完整SHA、路径及是否与原字节一致，见同名JSON。

| task | F1格式说明行 | F2 CLI行 | 最终结论 | instruction SHA256 | DATA SHA256 |
|---|---|---|---|---|---|
| smoke-test | — | — | 原无此问题；原审阅结论保留 | `5db2a8b566d920a2fac546e6f2fe79aec958aa2ecf753d3cfa63be5deac9794e` | `51a8607a52b9173f6816d9615422d4635d727385af03ee715bda01f884325b15` |
| case-grading-test | — | — | 原无此问题；原审阅结论保留 | `f35fcf8a7a97d4e24e9b56657d743fcdfabf312cb73344cb2b1e819793182530` | `47f6241a891866d6eab7801c7da6bea2f98c3e4ea1896a44de47019b4150211c` |
| darcy-flow-2d | 53 | — | F1解决；原入口保留 | `0fdabe2e235fad1192e5596034c3365817a336827ffa3442c086de5467fda3b7` | `0b9d78fe743716bd90600b2f038c657ae15392548f271b18d7a65235d6a39ec2` |
| heat-conduction-steady-2d | — | — | 原无此问题；原审阅结论保留 | `e8cc26fad2386b1eae3096ea24e266cea9177d33463a2c3f2878e87eaba78537` | `0ebddc4d16fd6f2c4e9580867cdf6885f88f467ab848f2d39dbb69c7e7fb2061` |
| diffusion-sorption-1d | 68 | — | F1解决；原入口保留 | `7a2f9c6820135bf19e08d70f0f671d24ca166db32a638add43147b8ec584e9f3` | `a891d70ccf780fbffb3d23656dcf42e4ecbfd14e2c0a2b6078c0ce81e50f224b` |
| heat-conduction-transient-2d | — | — | 原无此问题；原审阅结论保留 | `b828e787cafac7f9a0a90b4159c690d954068321ffccf98deaa864f76c081be6` | `8b8e8eaae4373ba80dfc0e0357b491bed4890b91e550c2c74dd46dcd1cae692c` |
| reaction-diffusion-1d | 56 | — | F1解决；原入口保留 | `a3ab26c430c41594ae1e07702bcd5c10ad87220669eee9c8b0d7b3917834ac01` | `6d1c350ecd002c0886e74208f740d7b1fa4e51ad7ded05e8d1d9f6e3c21b760f` |
| reaction-diffusion-2d | 61 | — | F1解决；原入口保留 | `0192e893bed95ec8b66b7e8b4da621b8843fc6ca061ff015f520911d272ca53b` | `37d727851940d721a40fe4cf7007dbbce91d4c34ca8f729369e953aedc228ddb` |
| advection-1d | 55 | — | F1解决；原入口保留 | `76c21cd3b327c58771d1f4f3d93e1ab951a59f140502273215add8d6c42959b2` | `8531cf967d5208907ccedb8758c2ca98d354174282c8d3a34388cc66bdaac3bf` |
| shallow-water-2d | 56 | — | F1解决；原入口保留 | `b7b5417e0d0322375c0b4d8c2851e7baf54ac77460dcd3f796259f4ab972f51b` | `2dd9fe46fcfcfb5325fea0d856e09bdf5a32d143a30ea1567c477a527d665d71` |
| burgers-1d | 55 | — | F1解决；原入口保留 | `e85b2bc8e44aebd580e26452854cd9e2c8328784e7637c40c80ebaeb814d0b8a` | `63bec17ceb291bad00d348519adc960b7512a41281e643ee1c794f8d84e4468f` |
| incompressible-navier-stokes-2d | 60 | — | F1解决；原入口保留 | `4d2302c649a69a853b22861d87f65dff7b6789b7944fefa59f72725bdcc2ba12` | `c5d70e638f7412ac9dcb6d629743fd74da261453ec1bf20114c7564b382e3b73` |
| compressible-navier-stokes-1d | 65 | — | F1解决；原入口保留 | `fd34ce717acb803e619c3ef568bc5edfd39b0a7327b3355618581ef69043c1df` | `377906b0f16c12d0a72465adef1d8c579028bb1507c1403b778eae5a3c98fef3` |
| compressible-navier-stokes-2d | 65 | — | F1解决；原入口保留 | `71b1e12f482cca51676e0b2bd44f44e7829f7a1ce1458a8dd42bacd6f829ef89` | `1d6c12880de18f433a864e059954d38a13de4488be247b61f436a3eb703e0c65` |
| compressible-navier-stokes-3d | 65 | — | F1解决；原入口保留 | `0bec9698201a5761c04ac57e5b393453c49a7692d597d2eb6d9268bf2c4050bf` | `cd1013f6f6b6bdb46f33b38dcfb3e86fb7b10004241ab7681e7128794a4f6824` |
| cc-1d-burgers-equation | 33 | 16 | F1/F2均解决 | `5e22f4bdedab669cd718eaeac2fc2a8b50d8f04d482a49f9f7b510f627cb7b3c` | `c4757d08649ca5e6677e977a35e9eaed5fcba4dd4842d035cb5aba629c1effb6` |
| cc-1d-diffusion | 33 | 16 | F1/F2均解决 | `6b33b07bd6a798ba487979dbb65eb10cfc2afae82df09bac8ed3e77527ecf266` | `fcc916fce23cf82b4d74c58807542bba83785127f07779aed59f85a3331655cc` |
| cc-1d-euler-shock-tube | 33 | 16 | F1/F2均解决 | `34905bb83594b2c34fd213b503e24db78a45db31a409f43aeca882476c305aa3` | `5bf5ba925302ceca722f3b17d9874a333ca83f3594c245b9653ffc0acef2900f` |
| cc-1d-linear-convection | 33 | 16 | F1/F2均解决 | `0c5dad257fc1cd96a3125a24e1e767c01952488348e96a66f0bab9214b2d2d5e` | `c15409d2290291e31c81d8b91b31fc4a42bbeac120c7f22b17a30c74424e6252` |
| cc-1d-nonlinear-convection | 33 | 16 | F1/F2均解决 | `01db71769c34f189dbe5f222ccf5553f4bcb34dcb8f64681ebd7914844453d0c` | `9c8c4359d6473a5c9dcab329cd112c1f91f13d23b6e978b7533a5c1f45a6c215` |
| cc-2d-burgers-equation | 33 | 16 | F1/F2均解决 | `1da4c2ecf1ac4d4e7b90222edb9e60f94f56c9ad84d5480e305ccbdf36fab711` | `6986bb1b468ed8bf345b05cda793cef58c72d426a9e348dcd302dfc713271971` |
| cc-2d-convection | 33 | 16 | F1/F2均解决 | `a65b8383f5114f8e293b76f350676a3468b9c4c32c339e7a89fc9ce607ae1716` | `9a1d30d15c07a5a88931f96fc487efe4476a5430efeccc1b51e0f9a54bf0f069` |
| cc-2d-diffusion | 33 | 16 | F1/F2均解决 | `e29e02d0fba9ff2c891d2af11a3bbab39826ad2ebd218bb7176bc09ef5880d90` | `1e20b41aa64ccdac0f9126620eb835ad6602251e91421547d0607701fb145085` |
| cc-2d-inviscid-burgers | 33 | 16 | F1/F2均解决 | `acde1ec87dd5b15007d7b2e76646b24c1539894aa2fd7f1ecb2dbc8d16291c95` | `8b6d89871c54a997005a464eb900e910a025538986a17d1bb04255def5565082` |
| cc-2d-laplace-equation | 33 | 16 | F1/F2均解决 | `da9a8593bc8522db45899998f64093a2bd61ddb72c7285dec859af036c21ceb8` | `1b61b3b12abbf0bd6908204edc68f7e577e47d5f64911c85701379a67f345210` |
| cc-2d-linear-convection | 33 | 16 | F1/F2均解决 | `bf58e7a7de6d42d5f68362e84e1e149c89c6db386de178110e093472a25ed36b` | `bb0034c16b97b3bbd462116178036cee74e8caf8954b6a7756e1a9a399b20b55` |
| cc-2d-navier-stokes-cavity | 33 | 16 | F1/F2均解决 | `9cd0cd5928b38f0407e995f9147a2fee5b761ee77ff2fb6ae3dee1b52486e6df` | `40bb2eb77158e3ee05561c5b7e1769fa5898ba732a9cc43777ca049256827fd3` |
| cc-2d-navier-stokes-channel | 33 | 16 | F1/F2均解决 | `d9eef56c2ea13c2fa11259a6da7e9b3a29f0a6e16393914e13630586287078e8` | `893a170598e251795fa7d9cf9ad99e5f30d445920c053a31f360fc9b0790e9d0` |
| cc-2d-poisson-equation | 33 | 16 | F1/F2均解决 | `5a16870b8c0afeea528b6bb4df87622cf148c9bb8578b0cfca36f149db846746` | `0566aecb5253a4f09a943dec9be1f97084319c617241c283a83ac7ab7dc1f15a` |
| cc-2d-steady-heat-equation | 33 | 16 | F1/F2均解决 | `e6c62e9a926ae7ab07f6d6719d3717a55350cdbdb974b2c64011ecbf6cccb880` | `c314a5d11e8e1470f4733f845b83d6bb74dd037ae30cef39d33d79433ae3daf6` |
| cc-2d-unsteady-heat-equation | 33 | 16 | F1/F2均解决 | `d59ac23c4c714b6843e0edefc8baae93ae68afda4b9b693b601fa7a62b1a62dd` | `8e92668b19e74b15797b68504dfd8b876c5ba6260e74f84b767fd8c697678645` |
| cc-fully-developed-turbulent-channel-flow | 33 | 16 | F1/F2均解决 | `4f3bc0b0988f2ac83c04b50a8761a14c6e7746102780e8429f9204903be0e88e` | `543aae19b43781a8a3a5597fde502f7e6632f3cd4281ea393f0a282cee92f916` |
| cc-lid-driven-cavity | 33 | 16 | F1/F2均解决 | `c6bb06a87af04ea0a7a036d468b3c0b10595506750015bd453e1a9a149629f12` | `ed23c0a6df04c00ff1555f4af252b1863523f349e0b768a43187401beca5fa05` |
| cc-flow-past-circular-cylinder | 33 | 16 | F1/F2均解决 | `d8cbd80c392a9db8f7f8624ea08c15a5aaf773d9f004189da11db008d7b475be` | `3e033270a728e58bb090920dffff9ff799ad5e2354c3ee2050897414f7d57e87` |
| cc-1d-kdv-burgers-equation | 33 | 16 | F1/F2均解决 | `33896ef7c0ef23e8a71f90bf0f133fcf68af5d3708575bf636938120dc85cf3e` | `639cae20cd3af28fc76e6ebc02acb87ee258c34da65ee1598725f815646f9950` |
| cc-2d-rayleigh-benard-convection | 33 | 16 | F1/F2均解决 | `6d2af32a681ca1a2a899b56b60117e24bcdeffb98d1cc713d277c175df0e55cd` | `677d347b9a60e3d5aa9ce25bb58d4dadacdcdfadd91676dc9ca671bd2b22242a` |
| cc-2d-shear-flow-with-tracer | 33 | 16 | F1/F2均解决 | `39835b50d15286a01340975b69f4eb6c7eff7e09b1f01dcedff9f7698ab9deeb` | `56567199939a10c3537e1a7775f72e746d7be9d510c7323a1bc35a14e1da598b` |
| cc-pipe-flow-disk-evp | 33 | 16 | F1/F2均解决 | `9e619ab70bb1c21633fac7755bcaa222dbe4068f25b4c4ddd485e67442efd40f` | `565680b12e0529bd9b57ca51f655cf8455e217cb1bbde30bd9c782d9b1ab7f7c` |
| cc-lane-emden-equation | 33 | 16 | F1/F2均解决 | `311ea30e739a931cdaf2434ca2420450f82ff1a7f494f97c026d84932380331c` | `796f9d2e02f8ada7340b6b85ece63b2796a74e351c8a0d7fca361013167a3a81` |

## 本结论的范围

本次认证公开材料的F1/F2修订闭环，不认证随机格式文件的数值正确性，也未运行solver、模型或重新生成参考。原审阅关于数值样例的局限、资源实测与隐藏判分尚未由考生独立认证的说明继续保留；它们不因本次窄复核自动转为通过。未读取作者实现、作者报告或隐藏case/reference。
