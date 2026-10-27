# z-life-hub：家庭生活管理后台

把日记、读书笔记、健康档案、各种凭证、记账、电脑管理装进一个 Agent，用一句话管全家的生活杂事。在 WorkBuddy 5.3.3 上实测，其他支持 Agent Skills 的环境同样适用

> **一键安装**：把这一页截图发给 WorkBuddy，说「帮我装上图里这些 skills」即可。Agent 按下面步骤执行：从 `https://github.com/tjxj/z-skills` 的 `z-life-hub/` 目录复制 5 个 Skill 文件夹到 `~/.workbuddy/skills/`，再执行 `npx skills add tjxj/ai-bookkeeping-skills` 装记账，最后新建 `~/Documents/LifeHub/` 并选为工作空间

所有数据默认放在本地 `~/Documents/LifeHub/`，全是 Markdown、CSV 和一个 SQLite 文件，换工具也能接着用

| Skill | 用途 | 典型触发 |
| --- | --- | --- |
| [`personal-diary`](personal-diary/SKILL.md) | 每天一个日记文件，原话一字不改，图片原样存档，可回查和出月度回顾 | 日记 xxx、记一下今天、我哪天做了什么 |
| [`reading-notes`](reading-notes/SKILL.md) | 每本书一个笔记，金句带页码，书单总表，读完出总结，年底出阅读报告 | 开始读《xx》、书摘、这本书读完了 |
| [`family-health-archive`](family-health-archive/SKILL.md) | 轻量家庭健康档案：报告按家人归进腾讯文档文件夹，只解读异常项，记一行总表 | 帮我存一下报告、解读一下化验单、上次尿酸多少 |
| [`voucher-vault`](voucher-vault/SKILL.md) | 发票、保修卡、合同、证件归档建索引，到期前 30 天提醒，证件号只记后 4 位 | 存一下这张凭证、保修还有多久、护照什么时候过期 |
| [`mac-butler`](mac-butler/SKILL.md) | Mac 只读体检：磁盘、内存、启动项、电池，出 HTML 报告，清理需确认且只进废纸篓 | 给电脑做个体检、磁盘满了、清理一下电脑 |

记账使用独立仓库 [`tjxj/ai-bookkeeping-skills`](https://github.com/tjxj/ai-bookkeeping-skills)（setup / record / ask / report 四个 Skill），后端选本地 SQLite：

```bash
npx skills add tjxj/ai-bookkeeping-skills
```

## 安装

```bash
npx skills add tjxj/z-skills --skill personal-diary
npx skills add tjxj/z-skills --skill reading-notes
npx skills add tjxj/z-skills --skill family-health-archive
npx skills add tjxj/z-skills --skill voucher-vault
npx skills add tjxj/z-skills --skill mac-butler
```

WorkBuddy 手动安装：把上面 5 个文件夹复制到 `~/.workbuddy/skills/`，在「专家·技能·连接器」→「我安装的」里能看到即可

## 使用前

1. 新建 `~/Documents/LifeHub/` 文件夹，在 Agent 里选它当工作空间
2. 想换数据目录，在各 `SKILL.md` 里全局替换 `~/Documents/LifeHub/`
3. 健康档案的成员（爸爸 / 妈妈 / 孩子）按自家实际改
4. 可选：WorkBuddy 连接器里连上「腾讯文档个人版」，健康档案会存进云端「家庭健康」文件夹；没连时自动退回本地
5. 健康档案只做信息整理，解读以医生面诊为准
