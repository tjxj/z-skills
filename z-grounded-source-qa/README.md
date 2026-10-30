# z-grounded-source-qa

`z-grounded-source-qa` 是一个面向任意本地资料库的证据型问答 Skill

它把访谈、会议纪要、研究笔记、网页采集结果、产品文档和已解析的 PDF 等资料，转换成可检索、可定位、可复核的回答依据

Skill 自身不内置某个人物或某一份资料，安装后可直接对新的 Markdown/TXT 语料工作

## 为什么取这个名字

- `grounded`：回答受来源约束，每个重要结论都要能落回证据
- `source`：资料由用户指定，边界清楚
- `qa`：覆盖问答、核对、总结、比较、写作和人物模拟等常见场景
- `z-`：与 `tjxj/z-skills` 的公开命名规范保持一致

## 适用场景

- 只根据一组访谈回答问题
- 从会议纪要中核对某项决策
- 比较两版政策、合同或产品文档
- 为文章、脚本、报告建立出处清楚的事实底稿
- 根据多份公开讲话做有边界的人物观点模拟
- 检查一段内容是否超出了原始资料
- 对本地知识库进行重复、稳定的证据检索

## 设计思路

### 1. 工作流与资料分离

固定人物资料会快速获得强效果，也会限制复用范围

本 Skill 只保存检索方法、证据规则和回答流程，真实语料通过 `--source` 在运行时传入

这样可以让同一个 Skill 服务于不同人物、项目、客户和行业，同时避免把私有资料发布进公开仓库

### 2. 检索与写作分层

整个流程分成四层：

1. **来源层**：用户明确指定 Markdown/TXT 文件或目录
2. **检索层**：多表达式召回、完整段落、排序、合并和去重
3. **证据层**：区分直接证据、综合判断、推断和证据缺口
4. **表达层**：根据用户要求输出自然回答、证据审计、文章或人物模拟

检索结果通过结构化 evidence object 交给后续推理，减少“找到一行就直接下结论”的随机性

### 3. 多表达式替代单关键词

用户问题里的用词经常与资料原文不同

例如用户问“怎么变现”，原文可能写成“付费转化”“收入结构”“商业模式”或“成本回收”

因此默认先生成 3–8 个表达式，再执行首轮检索

### 4. 完整语义段落

固定前后几行容易截断因果关系、限定条件和说话人

检索器按 Markdown 段落组织证据，并保留章节、页码、时间戳、说话人和行号

### 5. 二次检索是证据门槛

首轮只找到结论、没有找到原因或边界时，需要改写查询

增加返回条数无法补上缺失概念，因此二次检索要求更换表达式，搜索机制、风险、例外或反面证据

### 6. 查询未命中与资料缺失分开处理

一次关键词搜索没有结果，只能说明当前表达式没有命中

Skill 会提示增加同义词、改写查询或直接阅读相近章节，避免把检索失败写成资料结论

### 7. 本地、确定性、零第三方依赖

检索脚本只使用 Python 标准库，在本地读取 Markdown/TXT

它不上传资料，不依赖向量数据库，也不要求 API Key，适合先建立轻量、透明、可测试的证据闭环

## 安装

列出仓库内可安装 Skills：

```bash
npx skills add tjxj/z-skills --list
```

安装本 Skill：

```bash
npx skills add tjxj/z-skills --skill z-grounded-source-qa
```

## 把底座生成专用 Skill

这个版本新增了一个生成器，可以把底层检索能力、你的资料、专用回答规则和测试问题一起打包成独立 Skill

公式很简单：

```text
专用 Skill = 检索能力 + 有边界的资料 + 回答契约 + 测试问题
```

先把 PDF 转成带页码的 Markdown：

```bash
pdftotext -layout source.pdf extracted.txt

python3 scripts/prepare_pdftotext.py \
  extracted.txt prepared-source.md \
  --title "资料标题"
```

编号语录、编号制度可以增加 `--mode numbered`

再生成专用 Skill：

```bash
python3 scripts/create_specialized_skill.py \
  --name z-example-advisor \
  --title "示例顾问" \
  --mode advisor \
  --source prepared-source.md \
  --output-root "/path/to/.agent/skills" \
  --trigger "示例书籍" \
  --question "我现在最应该先做什么，为什么"
```

支持四种回答契约：

- `persona`：人物公开材料的第一人称模拟与受控推演
- `advisor`：书籍、课程、研究资料的框架提炼与行动指导
- `policy`：报销、差旅、请假、采购等制度预审
- `source-qa`：项目资料、访谈、会议纪要和混合知识库问答

生成结果自带检索脚本、内置语料、来源哈希、角色说明和 `evals.json`，复制整个目录就能使用

详细定制方法见 [references/specialization-guide.md](references/specialization-guide.md)

## 快速使用

```bash
python3 scripts/search_evidence.py \
  --source "/path/to/interviews" \
  --source "/path/to/project-notes.md" \
  --query "商业化" \
  --query "盈利" \
  --query "付费转化" \
  --query "成本回收" \
  --top-k 8 \
  --format json
```

目录会递归读取：

- `.md`
- `.markdown`
- `.txt`

## 证据对象

```json
{
  "evidence_id": "ev-6e3f7dd546c1",
  "score": 18,
  "matched_terms": ["商业化", "付费转化"],
  "content": "完整语义段落",
  "location": {
    "document": "interview.md",
    "line_start": 42,
    "line_end": 45,
    "page": 7,
    "timestamp": "00:12:34",
    "section": "商业模式",
    "speaker": "受访者"
  },
  "additional_locations": [],
  "block_ids": ["d001-b0012"],
  "previous_context": "前一段预览",
  "next_context": "后一段预览",
  "content_hash": "6e3f7dd546c1"
}
```

## 推荐的资料标记

Markdown 中可使用这些标记提升定位质量：

```markdown
# 访谈标题

## PDF Page 7

[00:12:34]

受访者: 这里是一段完整回答
```

也支持：

```markdown
<!-- page: 7 -->
```

详细格式见 [references/source-preparation.md](references/source-preparation.md)

## 能力边界

- 当前检索是透明的词法检索，适合规模可控的本地语料
- PDF、Word、图片和音视频需要先转换成 Markdown/TXT
- 同义词由 Agent 根据问题生成，脚本不调用外部模型
- 超大语料、跨语言语义检索或高召回要求，可在后续接入 embeddings 或全文索引
- 公开发布前仍需对高风险结论进行人工复核

## 验证结果

检索脚本包含 6 项自动化测试：

- 递归发现多个资料文件
- 多表达式覆盖排序
- 完整段落与位置元数据
- 相邻命中段落合并
- 重复内容去重并保留其他位置
- 查询未命中边界和显式正则检索

3 组行为评测覆盖产品变现、故障归因和政策版本比较：

- 使用 Skill：15/15 条断言通过
- 强基线：14/15 条断言通过
- 差异集中在结构化检索轨迹

小型资料对强 Agent 较容易，内容正确性在两组中都很高

因此本 Skill 的核心价值落在流程稳定性：把多表达式检索、证据对象、来源定位、二次检索和证据边界固化成可重复执行的标准步骤

## 目录结构

```text
z-grounded-source-qa/
├── SKILL.md
├── README.md
├── scripts/
│   ├── search_evidence.py
│   ├── prepare_pdftotext.py
│   └── create_specialized_skill.py
├── references/
│   ├── evidence-contract.md
│   ├── source-preparation.md
│   └── specialization-guide.md
├── tests/
│   └── test_search_evidence.py
└── evals/
    ├── evals.json
    └── fixtures/
```

## 定位与复用

`z-grounded-source-qa` 提供可复用的底层方法，适合任何新语料、人物或项目。
