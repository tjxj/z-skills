# z-life-hub：家庭生活管理后台

把日记、读书笔记、健康档案、各种凭证、记账、电脑管理装进一个 Agent，用一句话管全家的生活杂事。数据全部存进**腾讯文档**，手机腾讯文档 App、微信里随时能看、随时能记。在 WorkBuddy 5.3.3 上实测，其他支持 Agent Skills 并能连腾讯文档的环境同样适用

> **一键安装**：把这一页截图发给 WorkBuddy，说「帮我装上图里这些 skills」即可。Agent 按下面步骤执行：从 `https://github.com/tjxj/z-skills` 的 `z-life-hub/` 目录复制 6 个 Skill 文件夹到 `~/.workbuddy/skills/`，再提醒用户在「专家·技能·连接器 → 连接器」里授权「腾讯文档」

所有数据放在腾讯文档根文件夹「生活后台」下，第一次用时自动建好，本地不留文件

```
生活后台/
├── 日记/          每天一篇在线文档
├── 读书笔记/      一本书一篇 + 「书单」智能表格
├── 家庭健康/      爸爸 / 妈妈 / 孩子 + 「健康总表」智能表格
├── 凭证/          原件/YYYY/ + 「凭证索引」智能表格
├── 账本/          「家庭账本」智能表格 + 月报
└── 电脑体检/      每次体检一篇报告
```

| Skill | 用途 | 典型触发 |
| --- | --- | --- |
| [`personal-diary`](personal-diary/SKILL.md) | 每天一篇日记文档，原话一字不改，图片原样插入，可回查和出月度回顾 | 日记 xxx、记一下今天、我哪天做了什么 |
| [`family-ledger`](family-ledger/SKILL.md) | 一句话记账，自动拆笔、归类，先预览再入账，按月按类查账出月报 | 记一笔、花了、这个月吃饭花了多少 |
| [`reading-notes`](reading-notes/SKILL.md) | 每本书一篇笔记，金句带页码，书单总表，读完出一页纸总结和年度报告 | 开始读《xx》、书摘、这本书读完了 |
| [`family-health-archive`](family-health-archive/SKILL.md) | 报告按家人归档，只解读异常项，健康总表记一行，随时查 | 帮我存一下报告、解读一下化验单、上次尿酸多少 |
| [`voucher-vault`](voucher-vault/SKILL.md) | 发票、保修卡、合同、证件归档建索引，到期前 30 天提醒，证件号只记后 4 位 | 存一下这张凭证、保修还有多久、护照什么时候过期 |
| [`mac-butler`](mac-butler/SKILL.md) | Mac 只读体检：磁盘、内存、启动项、电池，报告存腾讯文档，清理需确认且只进废纸篓 | 给电脑做个体检、磁盘满了、清理一下电脑 |

## 安装

```bash
npx skills add tjxj/z-skills --skill personal-diary
npx skills add tjxj/z-skills --skill family-ledger
npx skills add tjxj/z-skills --skill reading-notes
npx skills add tjxj/z-skills --skill family-health-archive
npx skills add tjxj/z-skills --skill voucher-vault
npx skills add tjxj/z-skills --skill mac-butler
```

WorkBuddy 手动安装：把上面 6 个文件夹复制到 `~/.workbuddy/skills/`，在「专家·技能·连接器」→「我安装的」里能看到即可

## 使用前

1. WorkBuddy 连接器里授权「腾讯文档」（个人版），这是唯一的存储
2. 手机装腾讯文档 App 或用微信小程序，打开「生活后台」就能看全家的数据；想在手机上直接记，绑定 WorkBuddy 微信小程序后发消息即可
3. 健康档案的成员（爸爸 / 妈妈 / 孩子）按自家实际改
4. 健康档案只做信息整理，解读以医生面诊为准
