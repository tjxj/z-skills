"""二十四套材质。每套只定义颜色、字体、笔触、纹理和标题样式，不规定画面放什么。

灵感来源：Hallmark 的「材质不管结构」理念、Excalidraw、瑞士国际主义海报、包豪斯、
新粗野主义、Apple 便当格、Linear 暗色界面、ByteByteGo 式技术配图、孔版印刷、半调网点。
"""

SERIF = "'Source Han Serif SC','Source Han Serif SC VF','Noto Serif CJK SC','Noto Serif SC','Songti SC',STSong,serif"
KAI = "'LXGW WenKai','LXGW WenKai Mono','Kaiti SC',STKaiti,KaiTi,serif"
MONO = "'SF Mono','JetBrains Mono',Menlo,Consolas,monospace"
SANS = "'Source Han Sans SC','Noto Sans CJK SC','Noto Sans SC','Helvetica Neue',Arial,sans-serif"
HEAVY = "'Source Han Sans SC Heavy','Noto Sans CJK SC Black','Source Han Sans SC','Noto Sans CJK SC','Arial Black',sans-serif"

# 字段说明
# bg/panel/panel2: 底色、卡片色、次级卡片色    ink/muted/rule: 主文字与骨架线、次要文字、细线
# accent/accent2: 主、副强调色（文字颜色按对比度自动挑）
# shape: rect | rough 手绘 | cut 切角 | pixel 像素台阶      texture: dots grid lines grain scan paper halftone none
# header: rule | band 色带 | bar 左竖条 | highlight 荧光笔 | scribble 手绘线 | double | double-accent | thin | plain | seal 印章 | tag 图签 | prompt 光标
# shadow: 硬投影偏移   soft_shadow: 柔和投影   die: 贴纸白边   glow: 霓虹叠描   misreg: 套色错位   hachure: 斜线填充
# tones / tone_strokes: 节点按顺序轮换的填充色和描边色     deco: bauhaus stars blobs corner aurora
STYLES = {
    # ---- 技术向 ----
    "swiss": dict(
        cn="瑞士网格", bg="#F5F4EF", panel="#FFFFFF", panel2="#E9E7E0", ink="#121212", muted="#66645E",
        rule="#D3D0C7", accent="#E4572E", accent2="#121212", good="#1E8E3E", bad="#D93025",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=900, radius=4, stroke=2.2,
        shape="rect", texture="none", frame=0, shadow=0, header="rule", topbar=True,
        keywords="架构 工程 模型 推理 部署 技术 rag 开源 api 系统 原理 默认",
        note="暖白底、墨黑骨架、朱红顶条，技术长文的默认款"),
    "candy": dict(
        cn="糖果技术图", bg="#FFFFFF", panel="#FFFFFF", panel2="#F3F4F6", ink="#1F2937", muted="#6B7280",
        rule="#E5E7EB", accent="#F97316", accent2="#2563EB", good="#16A34A", bad="#DC2626",
        font_title=SANS, font_body=SANS, font_mono=MONO, title_weight=800, radius=14, stroke=2.2,
        shape="rect", texture="none", frame=0, shadow=0, header="rule",
        tones=["#DBEAFE", "#DCFCE7", "#FEF3C7", "#FCE7F3", "#EDE9FE", "#FFEDD5"],
        tone_strokes=["#3B82F6", "#22C55E", "#F59E0B", "#EC4899", "#8B5CF6", "#F97316"],
        keywords="系统设计 面试 架构 微服务 缓存 数据库 后端 云 kubernetes 分布式 消息队列",
        note="白底马卡龙色块配同色深描边，系统设计图解常见的那种清爽"),
    "blueprint": dict(
        cn="工程蓝图", bg="#123A6B", panel="#164577", panel2="#1C5089", ink="#EAF2FF", muted="#A9C1E0",
        rule="#2D5F96", accent="#FFD166", accent2="#7FD1FF", good="#7EE0A1", bad="#FF8A80",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=800, radius=0, stroke=1.8,
        shape="cut", texture="grid", frame=0, shadow=0, header="tag",
        keywords="硬件 芯片 协议 网络 网关 分层 蓝图 机制 结构 osi tcp 电路",
        note="蓝晒图纸、白色细线、黄色标注，讲机制和结构"),
    "terminal": dict(
        cn="终端绿屏", bg="#0B0F0C", panel="#101812", panel2="#16211A", ink="#C9F7D1", muted="#7FA889",
        rule="#21402B", accent="#3FB950", accent2="#F2CC60", good="#3FB950", bad="#F85149",
        font_title=MONO, font_body=MONO, font_mono=MONO, title_weight=700, radius=2, stroke=1.8,
        shape="rect", texture="scan", frame=0, shadow=0, header="prompt",
        keywords="命令行 cli 终端 shell 黑客 安全 日志 agent 编程 代码 git",
        note="黑底绿字、扫描线、等宽字体，适合 Agent、CLI、安全话题"),
    "linear": dict(
        cn="暗夜产品", bg="#0B0C10", panel="#15171D", panel2="#1D2028", ink="#EEEFF2", muted="#9298A3",
        rule="#2A2E38", accent="#8B7CFF", accent2="#3DD6C6", good="#4ADE80", bad="#F87171",
        font_title=SANS, font_body=SANS, font_mono=MONO, title_weight=700, radius=12, stroke=1.4,
        shape="rect", texture="none", frame=0, shadow=0, header="thin", deco="aurora", node_stroke="#343947",
        keywords="saas 产品 工具 效率 ai 助手 cursor 工作流 自动化 插件 mcp",
        note="近黑底、细描边、紫青微光，像 Linear、Raycast 那类产品官网"),
    "neon": dict(
        cn="霓虹夜", bg="#0A0F1F", panel="#11182E", panel2="#18213D", ink="#E6F1FF", muted="#8B98BD",
        rule="#243052", accent="#22D3EE", accent2="#F472B6", good="#4ADE80", bad="#F472B6",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=800, radius=12, stroke=2,
        shape="rect", texture="dots", frame=0, shadow=0, glow=True, header="rule",
        keywords="传播 网络 赛博 未来 神经 算力 数据流 实时 霓虹 gpu",
        note="深夜蓝底、青粉霓虹叠描，传播、网络、数据流"),
    "arcade": dict(
        cn="像素街机", bg="#1A0B2E", panel="#2A1450", panel2="#3A1D6B", ink="#F8F1FF", muted="#C3AEE6",
        rule="#4B2A80", accent="#FF3EA5", accent2="#34F5C5", yellow="#FFE14D", good="#34F5C5", bad="#FF3EA5",
        font_title=MONO, font_body=MONO, font_mono=MONO, title_weight=800, radius=0, stroke=3,
        shape="pixel", texture="scan", frame=0, shadow=5, shadow_color="#0D0518", header="rule", deco="stars",
        keywords="游戏 像素 复古 街机 关卡 闯关 升级 打怪 玩家 8bit",
        note="紫黑底、像素台阶角、粉青撞色，游戏化和闯关类内容"),
    # ---- 编辑与观点 ----
    "editorial": dict(
        cn="杂志社论", bg="#FBF8F1", panel="#FFFFFF", panel2="#F1ECE0", ink="#111111", muted="#6B6457",
        rule="#D8D0BF", accent="#C8102E", accent2="#111111", good="#1F7A4D", bad="#C8102E",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=900, radius=0, stroke=1.4,
        shape="rect", texture="lines", frame=0, shadow=0, header="double",
        keywords="观点 商业 趋势 历史 行业 报告 对比 财经 评论 时间线",
        note="米白纸、宋体、细线与一抹报刊红，讲观点、行业、时间线"),
    "poster": dict(
        cn="国际海报", bg="#EDEBE6", panel="#FFFFFF", panel2="#DCD9D2", ink="#111111", muted="#55534E",
        rule="#C4C0B7", accent="#E1251B", accent2="#1E3FAE", good="#1E3FAE", bad="#E1251B",
        font_title=HEAVY, font_body=SANS, font_mono=MONO, title_weight=900, radius=0, stroke=2.4,
        shape="rect", texture="none", frame=0, shadow=0, header="band", band="#E1251B", deco="corner",
        keywords="宣言 大事件 发布会 年度 盘点 榜单 重磅 数据 排名",
        note="顶部整块朱红色带、粗黑体、大数字，瑞士国际主义海报"),
    "newsprint": dict(
        cn="半调报纸", bg="#F3E7C4", panel="#FBF4DE", panel2="#EADBB0", ink="#2A1A12", muted="#6A5038",
        rule="#D3C08F", accent="#D93A1E", accent2="#1E5AA8", good="#1E5AA8", bad="#D93A1E",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=900, radius=0, stroke=2,
        shape="rect", texture="halftone", frame=0, shadow=4, shadow_color="#2A1A12", header="double",
        keywords="新闻 号外 事件 复盘 调查 揭秘 内幕 老照片 报道",
        note="泛黄新闻纸、红色半调网点、硬投影，复盘和事件调查"),
    "porcelain": dict(
        cn="杂志瓷蓝", bg="#F5F7FB", panel="#FFFFFF", panel2="#E4EAF6", ink="#14213D", muted="#5E6B8A",
        rule="#C9D3E8", accent="#1F3A93", accent2="#C08A2B", good="#1F3A93", bad="#B23A48",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=800, radius=4, stroke=1.4,
        shape="rect", texture="none", frame=1, shadow=0, header="double-accent",
        keywords="理财 复利 金融 投资 财务 收益 优雅 知识 保险",
        note="瓷白与钴蓝、细线与描金，金融理财和优雅的数据图"),
    "ember": dict(
        cn="余烬", bg="#16100C", panel="#211813", panel2="#2C211A", ink="#F3E6D3", muted="#B9A189",
        rule="#3A2B20", accent="#FF7A1A", accent2="#E8C170", good="#9BD17A", bad="#FF5A3C",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=900, radius=6, stroke=1.6,
        shape="rect", texture="grain", frame=0, shadow=0, header="bar",
        keywords="深度 长文 思考 故事 人物 创业 失败 教训 夜读",
        note="炭黑底、暖米字、橙色余火，适合深度长文和故事复盘"),
    # ---- 好玩、潮流 ----
    "sketch": dict(
        cn="白板手绘", bg="#FFFFFF", panel="#FFFFFF", panel2="#F1F3F5", ink="#1E1E1E", muted="#5C5F66",
        rule="#CED4DA", accent="#E8590C", accent2="#1971C2", good="#2F9E44", bad="#E03131",
        font_title=KAI, font_body=KAI, font_mono=KAI, title_weight=700, radius=10, stroke=2.2,
        shape="rough", texture="none", frame=0, shadow=0, hachure=True, header="scribble",
        tones=["#A5D8FF", "#FFEC99", "#B2F2BB", "#FFC9C9", "#D0BFFF", "#FFD8A8"],
        keywords="手绘 白板 excalidraw 草图 头脑风暴 思路 入门 小白 科普 解释",
        note="Excalidraw 式抖动线条 + 斜线填充 + 楷体，像在白板上边讲边画"),
    "brutal": dict(
        cn="新粗野", bg="#F6F3EC", panel="#FFFFFF", panel2="#FFE14D", ink="#0A0A0A", muted="#3F3F3F",
        rule="#0A0A0A", accent="#FF5470", accent2="#4D7CFE", yellow="#FFE14D", good="#00B67A", bad="#FF5470",
        font_title=HEAVY, font_body=SANS, font_mono=MONO, title_weight=900, radius=8, stroke=3,
        shape="rect", texture="none", frame=0, shadow=6, header="highlight", outline_ink=True,
        tones=["#FFE14D", "#7DF9C2", "#A5B4FF", "#FF9EBB", "#FFB86B"],
        keywords="独立开发 indie 黑客 一人公司 副业 上线 产品 增长 工具推荐 测评",
        note="粗黑描边、硬投影、荧光黄高亮，独立开发和工具测评"),
    "sticker": dict(
        cn="贴纸", bg="#F6EFE4", panel="#FFFFFF", panel2="#FFD84D", ink="#231F1C", muted="#5A524B",
        rule="#E2D7C6", accent="#E8318A", accent2="#B8E62E", good="#2E9E5B", bad="#E8318A",
        font_title=HEAVY, font_body=SANS, font_mono=MONO, title_weight=900, radius=18, stroke=2.5,
        shape="rect", texture="none", frame=0, shadow=6, die=True, header="rule", outline_ink=True,
        tones=["#FF8AC2", "#C6F432", "#FFFFFF", "#FFD84D", "#8FD3FF"],
        keywords="清单 好物 推荐 种草 合集 必备 盘点 收藏 小技巧 生活",
        note="白色模切边 + 硬投影 + 热粉青柠，种草清单和盘点"),
    "bauhaus": dict(
        cn="包豪斯", bg="#F1EADB", panel="#FFFFFF", panel2="#E6DCC6", ink="#1A1A1A", muted="#5A554C",
        rule="#CFC3A9", accent="#D7261E", accent2="#1D4E9E", yellow="#F2B90C", good="#1D4E9E", bad="#D7261E",
        font_title=HEAVY, font_body=SANS, font_mono=MONO, title_weight=900, radius=0, stroke=0,
        shape="rect", texture="none", frame=0, shadow=0, outline=False, header="rule", deco="bauhaus",
        tones=["#D7261E", "#1D4E9E", "#F2B90C", "#1A1A1A"],
        keywords="设计 艺术 结构 构成 几何 美学 包豪斯 理念 方法论",
        note="米色底、红蓝黄三原色实心块、几何装饰，设计与方法论"),
    "riso": dict(
        cn="孔版印刷", bg="#F6F1E7", panel="#FFFDF8", panel2="#F9D6E8", ink="#1D2A6B", muted="#535C8C",
        rule="#D9CFC0", accent="#FF48B0", accent2="#0078BF", good="#00A95C", bad="#FF48B0",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=900, radius=14, stroke=2,
        shape="rect", texture="grain", frame=0, shadow=0, misreg=True, header="rule",
        keywords="营销 增长 电商 漏斗 转化 品牌 运营 小红书 潮流 消费",
        note="荧光粉 + 联邦蓝套色错位、纸面颗粒，营销增长类话题"),
    "bento": dict(
        cn="便当格", bg="#EEF0F4", panel="#FFFFFF", panel2="#E2E5EC", ink="#1D1D1F", muted="#6E6E73",
        rule="#D2D2D7", accent="#0071E3", accent2="#FF6B35", good="#30A46C", bad="#E5484D",
        font_title=SANS, font_body=SANS, font_mono=MONO, title_weight=800, radius=22, stroke=0,
        shape="rect", texture="none", frame=0, shadow=0, outline=False, soft_shadow=True, header="plain",
        keywords="苹果 apple 发布 功能 亮点 iphone mac 产品介绍 特性 新功能",
        note="浅灰底、大圆角白卡片、无描边柔影，像苹果发布会的功能格"),
    "lavender": dict(
        cn="薰衣草", bg="#F4F0FC", panel="#FFFFFF", panel2="#E7DFFA", ink="#241A3B", muted="#6B5C8C",
        rule="#D7CCF0", accent="#6D3BEF", accent2="#FF6FAE", good="#1F9D74", bad="#E0457B",
        font_title=SANS, font_body=SANS, font_mono=MONO, title_weight=800, radius=16, stroke=1.6,
        shape="rect", texture="dots", frame=0, shadow=0, header="rule", node_stroke="#CBBDF2",
        keywords="心理 情绪 成长 女性 关系 自我 习惯 睡眠 冥想 疗愈",
        note="淡紫底、圆角白卡、紫粉点缀，心理成长和情绪类话题"),
    # ---- 教学与生活 ----
    "field": dict(
        cn="现场手册", bg="#EFE6D2", panel="#FBF6EA", panel2="#E3D7BC", ink="#14110F", muted="#5D5446",
        rule="#C9BB9C", accent="#D7263D", accent2="#1B3A8C", good="#1B3A8C", bad="#D7263D",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=900, radius=0, stroke=2.5,
        shape="cut", texture="none", frame=3, shadow=6, header="bar",
        keywords="流程 规范 操作 手册 sop 安全 检查 步骤 培训 工业",
        note="米白硬边、红蓝双色、厚描边硬投影，SOP 和操作规程"),
    "chalk": dict(
        cn="黑板粉笔", bg="#22332B", panel="#22332B", panel2="#2B4036", ink="#F1F1E8", muted="#B3C2B3",
        rule="#3F5A4C", accent="#F7E28B", accent2="#F4A7B9", good="#B7E4C7", bad="#F4A7B9",
        font_title=KAI, font_body=KAI, font_mono=KAI, title_weight=700, radius=8, stroke=2.2,
        shape="rough", texture="grain", frame=0, shadow=0, header="scribble",
        keywords="课堂 教学 生物 物理 化学 数学 循环 学生 考试 公式",
        note="墨绿黑板、粉笔抖线、黄粉两色，课堂讲原理"),
    "notebook": dict(
        cn="横线笔记", bg="#FFFDF6", panel="#FFFFFF", panel2="#FFF3C4", ink="#22313F", muted="#5E6B78",
        rule="#C9DCEB", accent="#E5484D", accent2="#2F6FDE", good="#2E9E5B", bad="#E5484D",
        font_title=KAI, font_body=KAI, font_mono=MONO, title_weight=700, radius=6, stroke=1.8,
        shape="rough", texture="paper", frame=0, shadow=0, header="scribble",
        tones=["#FFF3C4", "#DDF0FF", "#E3F7DF", "#FFE3E3"],
        keywords="笔记 学习 读书 复习 总结 知识点 考研 自学 课程",
        note="横线本、红色页边线、楷体手写，读书笔记和学习总结"),
    "inkwash": dict(
        cn="水墨朱印", bg="#F3EEE2", panel="#F8F4EA", panel2="#E6DECB", ink="#2B2B2B", muted="#6F6757",
        rule="#D3C8B0", accent="#B7352B", accent2="#4A5A55", accent_ink="#F8F4EA", good="#4A5A55", bad="#B7352B",
        font_title=KAI, font_body=SERIF, font_mono=SERIF, title_weight=700, radius=2, stroke=1.6,
        shape="rough", texture="grain", frame=0, shadow=0, header="seal",
        keywords="中国 古代 历史 文化 节气 诗词 哲学 茶 传统 国风",
        note="宣纸、淡墨、朱砂印，国风、历史、文化话题"),
    "kraft": dict(
        cn="牛皮纸便签", bg="#D9C3A0", panel="#FFF3B0", panel2="#F5E6C4", ink="#3B2A1A", muted="#5E4830",
        rule="#BFA67E", accent="#C2410C", accent2="#2F5D50", good="#2F5D50", bad="#C2410C",
        font_title=SERIF, font_body=KAI, font_mono=MONO, title_weight=900, radius=2, stroke=1.8,
        shape="rect", texture="grain", frame=0, shadow=4, tape=True, header="rule",
        tones=["#FFF3B0", "#FFD6C9", "#D7F0D2", "#D4E7FA"],
        keywords="咖啡 美食 旅行 手作 日常 家庭 小店 开店 菜谱",
        note="牛皮纸底、彩色便签、胶带，生活、小店、非技术话题"),
    "garden": dict(
        cn="植物园", bg="#F2F0E3", panel="#FFFDF5", panel2="#E2EAD2", ink="#1E3A2B", muted="#566B5A",
        rule="#CBD5BC", accent="#2F7D4F", accent2="#E07A3C", good="#2F7D4F", bad="#C4502A",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=800, radius=14, stroke=1.6,
        shape="rect", texture="none", frame=0, shadow=0, header="rule", deco="blobs",
        tones=["#DCEBCB", "#F6E3B4", "#F3D0C0", "#D3E4EC"], tone_strokes=["#2F7D4F", "#B7862B", "#C4502A", "#3C7A96"],
        keywords="植物 自然 环境 健康 饮食 农业 生态 气候 养生 户外",
        note="米绿底、叶片色块、自然配色，健康、自然、生态话题"),
}

DEFAULT_STYLE = "swiss"


def pick_style(text, fallback=DEFAULT_STYLE):
    """按主题文字里的关键词给风格打分，分数最高的胜出。"""
    t = (text or "").lower()
    best, score = fallback, 0
    for name, st in STYLES.items():
        s = sum(t.count(k) for k in st["keywords"].split() if k != "默认")
        if s > score:
            best, score = name, s
    return best
