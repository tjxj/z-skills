---
name: mac-butler
description: Mac 电脑管家。说「电脑体检」「电脑好卡」「磁盘满了」「清理一下电脑」「哪些开机启动」「找大文件」「重复文件」「电池怎么样」「整理下载文件夹」时触发。先体检出报告，任何删除、移动、关闭启动项都要用户确认。
---

# Mac 电脑管家

报告目录：`~/Documents/LifeHub/电脑管家/报告/`

## 一、体检（只读，可以直接做）

依次收集，命令失败就跳过并在报告里注明：

| 项目 | 命令 |
|---|---|
| 系统与机型 | `sw_vers`、`sysctl -n machdep.cpu.brand_string`、`system_profiler SPHardwareDataType` |
| 磁盘 | `df -h /`、`du -sh ~/Downloads ~/Desktop ~/Documents ~/Library/Caches 2>/dev/null` |
| 大文件 | `find ~ -xdev -type f -size +1G 2>/dev/null`（跳过 Library/Mobile Documents） |
| 内存/CPU 占用前 10 | `ps -Ao pid,pcpu,pmem,comm -r | head -11` |
| 开机启动 | `ls ~/Library/LaunchAgents /Library/LaunchAgents`、`osascript -e 'tell application "System Events" to get the name of every login item'` |
| 电池 | `pmset -g batt`、`system_profiler SPPowerDataType` 里的循环次数和健康度 |
| 下载文件夹 | 按扩展名统计数量和体积，列出 90 天未打开的文件 |
| 开发缓存 | `du -sh ~/Library/Caches/* ~/.npm ~/.cache ~/Library/Developer 2>/dev/null | sort -hr | head -15` |

体检结果生成单文件 `体检-YYYY-MM-DD.html`：总评分、磁盘饼图、可回收空间清单（按「安全可删 / 需你判断 / 别动」三档）、启动项清单、电池健康，最后给出 3 条最值得做的建议

## 二、清理（必须确认）

- 列出要处理的文件和预计释放空间，等用户回复「确认」再执行
- 删除一律用移到废纸篓（`osascript -e 'tell application "Finder" to delete POSIX file "路径"'`），**禁止 rm -rf**
- 系统目录、/System、/Library、iCloud 目录、照片图库、任何 .git 目录一律不碰
- 执行后再跑一次 `df -h /`，报告实际释放了多少

## 三、整理下载文件夹

按类型分到 `~/Downloads/{安装包,文档,图片,视频,压缩包,其他}`，先给出移动清单，确认后执行
