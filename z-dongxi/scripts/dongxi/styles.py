"""十二套材质。每套只定义颜色、字体、笔触和纹理，不规定画面放什么。"""

SERIF = "'Source Han Serif SC','Source Han Serif SC VF','Noto Serif CJK SC','Noto Serif SC','Songti SC',STSong,serif"
KAI = "'LXGW WenKai','LXGW WenKai Mono','Kaiti SC',STKaiti,KaiTi,serif"
MONO = "'SF Mono','JetBrains Mono',Menlo,Consolas,monospace"
SANS = "'Source Han Sans SC','Noto Sans CJK SC','Helvetica Neue',Arial,sans-serif"

# 字段说明
# bg/panel/panel2: 底色、卡片色、次级卡片色
# ink/muted/rule: 主文字与骨架线、次要文字、细线
# accent/accent2/accent_ink: 主强调色、副强调色、强调色上的文字
# shape: rect 圆角 | rough 手绘 | cut 切角
# texture: dots | grid | lines | grain | scan | none
# shadow: 硬投影偏移（0 为无）  glow: 霓虹叠描  misreg: 孔版错位  hachure: 斜线填充
# tones: 手绘风的节点填充色轮换
STYLES = {
    "swiss": dict(
        cn="瑞士网格", bg="#F8FAFC", panel="#FFFFFF", panel2="#E2E8F0", ink="#0F172A", muted="#64748B",
        rule="#CBD5E1", accent="#D97757", accent2="#0F172A", accent_ink="#FFFFFF", good="#16A34A", bad="#DC2626",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=900, radius=6, stroke=2,
        shape="rect", texture="dots", frame=2, shadow=0,
        keywords="架构 工程 agent 模型 推理 部署 技术 rag 开源 api 系统 默认",
        note="冷灰底、墨黑骨架、陶土橙流光，技术长文的默认款"),
    "sketch": dict(
        cn="白板手绘", bg="#FFFFFF", panel="#FFFFFF", panel2="#F1F3F5", ink="#1E1E1E", muted="#5C5F66",
        rule="#CED4DA", accent="#E8590C", accent2="#1971C2", accent_ink="#FFFFFF", good="#2F9E44", bad="#E03131",
        font_title=KAI, font_body=KAI, font_mono=KAI, title_weight=700, radius=10, stroke=2,
        shape="rough", texture="none", frame=0, shadow=0, hachure=True,
        tones=["#A5D8FF", "#FFEC99", "#B2F2BB", "#FFC9C9", "#D0BFFF", "#FFD8A8"],
        keywords="手绘 白板 excalidraw 草图 头脑风暴 思路 入门 小白 科普 解释",
        note="Excalidraw 式抖动线条 + 斜线填充 + 楷体，像在白板上边讲边画"),
    "blueprint": dict(
        cn="工程蓝图", bg="#123A6B", panel="#164577", panel2="#1C5089", ink="#EAF2FF", muted="#9FB8D9",
        rule="#2D5F96", accent="#FFD166", accent2="#7FD1FF", accent_ink="#123A6B", good="#7EE0A1", bad="#FF8A80",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=800, radius=0, stroke=1.6,
        shape="cut", texture="grid", frame=0, shadow=0,
        keywords="硬件 芯片 协议 网络 网关 分层 蓝图 机制 原理 结构 osi tcp",
        note="蓝晒图纸、白色细线、黄色标注，讲机制和结构"),
    "terminal": dict(
        cn="终端绿屏", bg="#0D1117", panel="#111820", panel2="#161F2A", ink="#C9F7D1", muted="#6E8F78",
        rule="#21402B", accent="#3FB950", accent2="#F2CC60", accent_ink="#0D1117", good="#3FB950", bad="#F85149",
        font_title=MONO, font_body=MONO, font_mono=MONO, title_weight=700, radius=2, stroke=1.6,
        shape="rect", texture="scan", frame=0, shadow=0,
        keywords="命令行 cli 终端 shell 黑客 安全 日志 agent 编程 代码 git",
        note="黑底绿字、扫描线、等宽字体，适合 Agent、CLI、安全话题"),
    "riso": dict(
        cn="孔版印刷", bg="#F4EFE6", panel="#FFFDF8", panel2="#F9D6E8", ink="#1D2A6B", muted="#5B6391",
        rule="#D9CFC0", accent="#FF48B0", accent2="#0078BF", accent_ink="#FFFFFF", good="#00A95C", bad="#FF48B0",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=900, radius=14, stroke=2,
        shape="rect", texture="grain", frame=0, shadow=0, misreg=True,
        keywords="营销 增长 电商 漏斗 转化 品牌 运营 小红书 潮流 消费",
        note="荧光粉 + 联邦蓝套色错位、纸面颗粒，营销增长类话题"),
    "editorial": dict(
        cn="杂志社论", bg="#FBF8F1", panel="#FFFFFF", panel2="#F1ECE0", ink="#111111", muted="#6B6457",
        rule="#D8D0BF", accent="#C8102E", accent2="#111111", accent_ink="#FFFFFF", good="#1F7A4D", bad="#C8102E",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=900, radius=0, stroke=1.4,
        shape="rect", texture="lines", frame=0, shadow=0,
        keywords="观点 商业 趋势 历史 行业 报告 对比 财经 评论 时间线",
        note="米白纸、宋体、细线与一抹报刊红，讲观点、行业、时间线"),
    "field": dict(
        cn="现场手册", bg="#EFE6D2", panel="#FBF6EA", panel2="#E3D7BC", ink="#14110F", muted="#5D5446",
        rule="#C9BB9C", accent="#D7263D", accent2="#1B3A8C", accent_ink="#FFFFFF", good="#1B3A8C", bad="#D7263D",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=900, radius=0, stroke=2.5,
        shape="cut", texture="none", frame=3, shadow=6,
        keywords="流程 规范 操作 手册 sop 安全 检查 步骤 培训 工业",
        note="米白硬边、红蓝双色、厚描边硬投影，SOP 和操作规程"),
    "neon": dict(
        cn="霓虹夜", bg="#0A0F1F", panel="#11182E", panel2="#18213D", ink="#E6F1FF", muted="#7D8BB0",
        rule="#243052", accent="#22D3EE", accent2="#F472B6", accent_ink="#0A0F1F", good="#4ADE80", bad="#F472B6",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=800, radius=12, stroke=2,
        shape="rect", texture="dots", frame=0, shadow=0, glow=True,
        keywords="传播 网络 赛博 ai 未来 神经 算力 数据流 实时 霓虹",
        note="深夜蓝底、青粉霓虹叠描，传播、网络、数据流"),
    "porcelain": dict(
        cn="杂志瓷蓝", bg="#F5F7FB", panel="#FFFFFF", panel2="#E4EAF6", ink="#14213D", muted="#5E6B8A",
        rule="#C9D3E8", accent="#1F3A93", accent2="#C08A2B", accent_ink="#FFFFFF", good="#1F3A93", bad="#B23A48",
        font_title=SERIF, font_body=SERIF, font_mono=MONO, title_weight=800, radius=4, stroke=1.4,
        shape="rect", texture="none", frame=1, shadow=0,
        keywords="理财 复利 金融 投资 财务 数据 增长 优雅 知识",
        note="瓷白与钴蓝、细线与描金，金融理财和优雅的数据图"),
    "chalk": dict(
        cn="黑板粉笔", bg="#22332B", panel="#22332B", panel2="#2B4036", ink="#F1F1E8", muted="#A9B8A9",
        rule="#3F5A4C", accent="#F7E28B", accent2="#F4A7B9", accent_ink="#22332B", good="#B7E4C7", bad="#F4A7B9",
        font_title=KAI, font_body=KAI, font_mono=KAI, title_weight=700, radius=8, stroke=2.2,
        shape="rough", texture="grain", frame=0, shadow=0,
        keywords="课堂 教学 生物 物理 化学 数学 循环 原理 学生 考试",
        note="墨绿黑板、粉笔抖线、黄粉两色，课堂讲原理"),
    "inkwash": dict(
        cn="水墨朱印", bg="#F3EEE2", panel="#F8F4EA", panel2="#E6DECB", ink="#2B2B2B", muted="#7A7262",
        rule="#D3C8B0", accent="#B7352B", accent2="#4A5A55", accent_ink="#F8F4EA", good="#4A5A55", bad="#B7352B",
        font_title=KAI, font_body=SERIF, font_mono=SERIF, title_weight=700, radius=2, stroke=1.6,
        shape="rough", texture="grain", frame=0, shadow=0,
        keywords="中国 古代 历史 文化 节气 诗词 哲学 茶 传统 国风",
        note="宣纸、淡墨、朱砂印，国风、历史、文化话题"),
    "kraft": dict(
        cn="牛皮纸便签", bg="#D9C3A0", panel="#FFF3B0", panel2="#F5E6C4", ink="#3B2A1A", muted="#6E5638",
        rule="#BFA67E", accent="#C2410C", accent2="#2F5D50", accent_ink="#FFFFFF", good="#2F5D50", bad="#C2410C",
        font_title=SERIF, font_body=KAI, font_mono=MONO, title_weight=900, radius=2, stroke=1.8,
        shape="rect", texture="grain", frame=0, shadow=4, tape=True,
        tones=["#FFF3B0", "#FFD6C9", "#D7F0D2", "#D4E7FA"],
        keywords="生活 咖啡 美食 旅行 手作 日常 家庭 小店 创业 清单",
        note="牛皮纸底、彩色便签、胶带，生活、小店、非技术话题"),
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
