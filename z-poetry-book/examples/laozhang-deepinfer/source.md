---
title: .md
author:
  - 老章 mlpy
date: 2026-10-25
categories:
  - AIGC
tags:
  - aigc
render_with_liquid: false
---

大家好，我是 Ai 学习的老章

前些天 DeepSeek 放出了 DeepSeek V4.1 Flash 1017 ，把性价比发挥到极致

之后他们还开源了自家的生产级推理引擎 DeepInfer，号称单卡每小时狂赚 38 刀、单集群日吞吐 155 万亿 Token，这个对业界的影响也很巨大

老章本职工作是大模型基建，平时打交道最多的是通用推理引擎 vLLM、SGLang，几乎所有大模型问世，他们都可以无缝适配，T0就能放出新版本，一键完成模型部署

更早之前我还介绍一个大模型推理新星 Strata，它通过“料理台（显存）与储藏室（内存/SSD）”的三级分层调度，把千亿 MoE 巨无霸塞进了普通消费级显卡甚至游戏本里，让单卡跑出上百 Token/s 的惊人速度

我在 Colab 中的英伟达 A100 上做过测试，推理速度属实惊人：[推理引擎新王？消费级显卡跑千亿大模型，Qwen3.8-Flash-Next本地部署，实测超快！](https://mp.weixin.qq.com/s/9jWHcbQlUZwFnZknS9pwdw)

![](https://r2.zhanglearning.com/blog/2026/10/ebdb66981dfbb490366c5651ba64c7e1.png)

当时不少同行讨论：大模型的工程生态是不是要变天了？以后的模型是不是都得带个像 DeepInfer 这样的“专属推理引擎”？通用推理框架 vLLM 和 SGLang 是不是要被动摇甚至被边缘化了？

刚刚，SGLang 和 vLLM 的新动作就到了，两家几乎在同一时间宣布：在 DeepSeek-V4.1-Flash 上的推理效率，双双追平甚至部分反超 DeepInfer

我感觉 vLLM 和 SGLang 雄厚的底蕴还是难以撼动的

### 通用引擎的硬核成绩单

这次 SGLang 和 vLLM 拿出来的测试数据用的全部是 DeepInfer 官方相同的测试标准和真实硬件基准

先看 **SGLang：

- **Prefill（输入预填充）**：在 4x GB300 和 4x B300 硬件上，SGLang 的 Prefill 吞吐量达到了 DeepInfer 的 1.04 倍，在 4K、32K 和 64K 新输入 Token 档位全面领先，8K 与 16K 持平
- **Decode（生成解码）**：在 64 张 GB300（EP64）超节点集群中，当并发在单卡 16 到 256 请求区间时，SGLang 的单步生成耗时比 DeepInfer 缩短了 1.1% 到 7.4%，在 8 并发时持平

![](https://r2.zhanglearning.com/blog/2026/10/e7834cc0d19e7d8eb35223ed875ac5be.png)

再看 **vLLM** ：

- **集群吞吐与成本**：在英伟达单台 GB300 NVL72 机架上，通过 PD 分离与 Wide-EP 超宽专家并行，在 SemiAnalysis AgentX 真实 Agent 轨迹评测中跑出了 **954K tokens/s 每卡** 的恐怖吞吐（P90 单用户达 196 tokens/s），相比单节点结果狂暴提升了 7.9 倍
- **单卡创收打平**：如果按照 DeepSeek 官方公布的谷时价格与实际吞吐折算，vLLM 在 GB300 上的产出折合 **每卡每小时 38.96 美金**，微超了 DeepSeek 之前公布的 38 刀标杆
- **对决 DeepInfer 官方曲线**：在 GB200 上测试 Decode（131K 上下文，nextn=3），在 Batch Size 8 到 256 的大范围下，vLLM 的输出吞吐与 DeepInfer 官方公布数据的差距缩窄到了 6% 以内；在 GB300 上，DEP2 的 Prefill 曲线全程紧贴 DeepInfer 官方发布线
- **单用户极速**：针对中小批次低延迟场景定制了专用的 Decode 路径，单用户 P90 速度直接狂飙到了 **826 tokens/s**

通用引擎不仅没被甩开，反而在短短几天内就把这个新霸主咬得死死的

### 这波狂暴提速是怎么做到的？

很多人纳闷：DeepSeek 花了无数心血软硬件一体调优出来的专用引擎，怎么短短几天就被两大通用框架迎头赶上了？

老章仔细研读了两家的技术拆解报告，核心秘诀其实就是两句话：**全面吸收 DeepSeek 开源的底层算子矩阵**，再加上**针对模型特性的工程极致打磨**

#### 1. 底层算子全盘整合：Mega 系列与 TileLang

DeepSeek 在开源 DeepInfer 的同时，一并贡献了整套高性能算子库，而 SGLang 和 vLLM 第一时间把它们全搬进了主线代码：

- 包括 FlashMLA、DeepGEMM、DeepEP、DeepSelect 以及 TileLang 系列高效算子
- 尤其是重头戏 **Mega 系列算子**：MegaMoE 把以往分散的 Token 路由分发、专家 GEMM 矩阵乘法和结果合并整合成了一个融合算子，大幅减少了 GPU 显存中间换入换出；MegaAttention 也直接成为了 Blackwell B300/GB300 上的默认注意力路径

![](https://r2.zhanglearning.com/blog/2026/10/0da88adecb97b51696edaf55093aa298.png)

#### 2. 吃透模型结构特性：DEP2 与 Wide-EP

盲目堆并行规模往往适得其反，两家框架在实际评测中都精准击中了 DeepSeek-V4.1-Flash 的架构特性：

- **KV Cache 极轻量**：因为采用了跨层 KV 共享和 FP4 压缩，全局 KV Cache 每 Token 仅仅占用 890 字节，显存容量根本不再是 Batch Size 的瓶颈
- **Prefill 规模宜小（DEP2 最优）**：vLLM 实测发现，在 Prefill 阶段用 DEP2（2卡专家+数据并行）每卡吞吐能达到 64.4K tokens/s，而盲目上 DEP4 吞吐反而跌到 53.3K，因为 4 卡间的数据并行（DP）不平衡会导致 13.6% 的性能损耗，反倒是 DEP2 最稳最轻快
- **Decode 必须走 Wide-EP**：评测表明，即使上下文长达 128K，生成阶段 62% 的耗时依然卡在 MoE 权重读取上，Attention 和 Indexer 加起来才占 13%；上下文从 128K 暴增到 855K，单步前向耗时仅仅增加了 7%（8.93ms 到 9.53ms），因此通过 Wide-EP 配合 EPLB 动态专家均衡调度，是榨干多卡带宽的唯一正解

#### 3. 算法层面的硬核剪枝：SWA 有界重放与 Engram 大页

DeepSeek 官方设计的几项算法绝活，通用框架在实现时甚至做了进一步的改良：

- **SWA Bounded Replay（滑动窗口有界重放）**：长文本下只重算最后 128 个 Token，SGLang 完美支持了解码重放与前缀命中编码重放；vLLM 更绝，把原本需要全量计算的 Layer 20 也做了重放改造，光这一项就让 32K 新 Token 的 Prefill 吞吐直接提升了 19.9%

![](https://r2.zhanglearning.com/blog/2026/10/f202cd072b3fa3d0dafe156d04f07156.png)

- **Engram 词表放置与内存大页**：SGLang 实现了主机内存共享（保留最多 HBM 给 KV）和跨 GPU NVLink 直读（Peer Shards，无需 All-Gather）；vLLM 则把原先 `/dev/shm` 容易引发 GPU TLB miss 的 64KB 小页，升级为 host-NUMA cuMem 2MB 大页，再次抠出 2.8% 的 Prefill 提升

![](https://r2.zhanglearning.com/blog/2026/10/8a0560054893dc7720ddb919e64aaf69.png)

- **异步调度重叠执行**：在 GPU 执行第 N 步时，CPU 已经提前把第 N+1 步的调度逻辑算好，消除了主机与设备端的等待气泡，其实早在 2024 年 12 月的 SGLang v0.4 中就已经奠定了这套 Zero-overhead 设计，连 DeepInfer 官方文档都明确注明借鉴了 SGLang

![](https://r2.zhanglearning.com/blog/2026/10/4bc4a8f83fdb2cd5397d8509df66b5e9.png)

### 关键点：DeepInfer 并不是一套完整系统

很多人前几天被 DeepInfer 的数据冲昏了头脑，但如果仔细读过 DeepInfer 项目的 README，就会发现官方自己写得很清楚：

**DeepInfer 目前主要是一套离线（Offline）推理引擎与底层算子集，并没有包含现代生产级线上服务所需的完整系统层**

SGLang 团队更是一针见血地指出了 DeepInfer 尚未开放、但生产环境不可或缺的三大核心组件：

![](https://r2.zhanglearning.com/blog/2026/10/9193650d91f4184edd2b770693965a96.png)

1. **工业级分布式 KV Cache 系统**：真实生产环境全靠跨轮次、跨用户的缓存复用来降低成本，SGLang 拥有打磨成熟的 RadixAttention 树状缓存，并通过 Linker 直连 GPU L1 本地显存与 3FS / Mooncake 等 L3 分布式闪存，甚至支持主机内存 L2 级 HiCache
2. **生产级 Prefill / Decode 分离架构**：把计算密集的 Prefill 机器和访存密集的 Decode 机器物理切开，中间依赖极高吞吐的 RDMA 网络传输，SGLang 完整支持 Mooncake、NIXL、MORI 等成熟传输后端
3. **多实例集群路由与负载均衡**：面对海量用户请求，网关层必须能根据缓存前缀命中做智能请求分发，避免快慢不均，这也是通用框架的看家本领
4. **多模型与跨硬件兼容能力**：DeepInfer 是为单模型高度定制的，而 SGLang 和 vLLM 不仅能跑 DeepSeek，还能跑 Llama、Qwen、Kimi、GLM；不仅支持英伟达 Hopper / Blackwell（GB300、B300、B200、H200），还适配了 AMD MI355X 以及国产算力集群

这才是企业真正能在生产环境中放心跑起来的“工业级底座”

无论是端侧极限优化的 Strata，还是云端极致压榨的 DeepInfer，这些专门为特定模型量身定制的“新锐框架”，确实在短时间内给通用框架带来了前所未有的压力

过去很长一段时间，大家的惯性思维是：大模型推理有 vLLM 和 SGLang 就够了，模型出来打个权重包，通用引擎套上就能跑

但当大模型演进到极其怪异的专属架构——细粒度动态 MoE、FP4 混合精度、跨层共享 KV、有界重放、超大外部词表时，通用框架如果反应慢上半拍，性能就会被专属引擎拉开两三倍的巨大鸿沟

### 未来很多模型都会有专属推理引擎吗？

结合目前大模型与系统工程的演进现状，老章在这里给出三点预判：

#### 预判一：算法与算子的“软硬协同设计”已成必然，但绝大多数厂商不会去做完整推理引擎

模型训练如果脱离了推理工程的考量，在商业化上几乎等于慢性自杀

不管是 DeepSeek 的 FlashMLA 和 Mega 系列，还是月之暗面 Kimi 的 MegaKernel，亦或是智谱的 HiSparse，顶尖模型团队在立项和预训练阶段，就必须和底层 CUDA/Triton 算子工程师坐在一起协同设计

但是，**“写出一批极致高效的模型算子”跟“做出一套生产级分布式推理引擎”，完全是两码事**

写几个定制算子加一个离线跑分脚本，充其量只占整个推理体系 15% 的工作量；剩下的 85% 全是分布式 KV 传输调度、容错重试、动态显存分页、网络通信优化、API 协议兼容和异构硬件适配

绝大多数模型厂商既没有这样庞大的系统工程团队，也没有必要在这个非核心赛道上重复造轮子

#### 预判二：未来的标准范式将是“模型厂开源定制算子，通用引擎负责承接与工业化”

DeepSeek 这次开源 DeepInfer，很多人只看到了一个跑分极高的引擎，但我看到的是一个极其成熟的产业分工信号：

DeepSeek 把自己经过真金白银验证的底层算子矩阵（FlashMLA、DeepGEMM、DeepEP、Mega 系列）毫无保留地推向社区，实际上是把最佳实践做成了开源公共品

而 vLLM 和 SGLang 这样拥有全球数百名核心贡献者的通用基础设施，可以在 72 小时内以极高的效率把这些算子全部吸收进去，直接赋能给全球无数现成的企业集群

这种“厂商出前沿算子 + 社区做通用承接”的模式，效率远高于每家厂商各自画地为牢维护一套小众引擎

#### 预判三：格局将呈现“端侧极客定制化”与“云端工业基础设施”的双轨制

未来推理生态的大格局基本清晰了：
- **端侧/个人玩家生态**：像 Strata 这样针对极致显存压缩、内存分级加载的小巧专用工具，会长期活跃在各种极客设备和消费级显卡上，因为通用大集群框架很难为了单张游戏卡去专门做深度剪裁
- **云端/企业生产环境**：以 vLLM 和 SGLang 为核心的通用推理双雄地位依然坚如磐石，它们会像操作系统界的 Linux 一样，不断吞噬融合各个厂商最优秀的单点创新，同时保持对多硬件、多模型、大规模集群的稳健支撑

技术永远在日新月异，但开源生态最具魅力的地方，从来都不是某一家的一骑绝尘，而是这种前浪刚掀起波澜、后浪便在几天之内百川汇海的生命力
