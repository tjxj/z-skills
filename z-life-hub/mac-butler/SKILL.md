---
name: mac-butler
description: Mac 电脑管家。说「电脑体检」「电脑好卡」「磁盘满了」「清理一下电脑」「哪些开机启动」「找大文件」「电池怎么样」「整理下载文件夹」时触发。先体检出报告存进腾讯文档，任何删除、移动、关闭启动项都要用户确认。
---

# Mac 电脑管家

体检命令在本机跑，**报告存腾讯文档**「生活后台/电脑体检/」，本地不留报告文件；手机上也能翻历次体检

## 一、体检（只读，可以直接做）

依次收集，命令失败就跳过并在报告里注明：

| 项目 | 命令 |
|---|---|
| 系统与机型 | `sw_vers`、`sysctl -n machdep.cpu.brand_string` |
| 磁盘 | `df -h /`、`du -sh ~/Downloads ~/Desktop ~/Documents ~/Library/Caches 2>/dev/null` |
| 大文件 | `find ~ -xdev -type f -size +1G 2>/dev/null`（跳过 Library/Mobile Documents） |
| 内存/CPU 占用前 10 | `ps -Ao pid,pcpu,pmem,comm -r | head -11`、`sysctl vm.swapusage` |
| 开机启动 | `ls ~/Library/LaunchAgents /Library/LaunchAgents` |
| 电池 | `pmset -g batt`、`system_profiler SPPowerDataType` 里的循环次数和健康度 |
| 下载文件夹 | 按扩展名统计数量和体积 |
| 开发缓存 | `du -sh ~/Library/Caches/* ~/.npm ~/.cache 2>/dev/null | sort -hr | head -15` |

体检结果写成在线文档 `体检-YYYY-MM-DD`，放进「生活后台/电脑体检/」：总评分（100 分制）、磁盘占用、可回收空间清单（按「安全可删 / 需你判断 / 别动」三档）、启动项清单、电池健康，最后 3 条最值得做的建议。回执里给出文档链接和总评分

## 二、清理（必须确认）

- 列出要处理的文件和预计释放空间，等用户回复「确认」再执行
- 删除一律移到废纸篓（`osascript -e 'tell application "Finder" to delete POSIX file "路径"'`），**禁止 rm -rf**
- 系统目录、/System、/Library、iCloud 目录、照片图库、任何 .git 目录一律不碰
- 执行后再跑一次 `df -h /`，把实际释放了多少追加到当天体检文档末尾

## 三、整理下载文件夹

按类型分到 `~/Downloads/{安装包,文档,图片,视频,压缩包,其他}`，先给出移动清单，确认后执行
