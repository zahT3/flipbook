# 用到的外部素材

| 素材 | 用在哪 | 来源 | 许可证 |
|---|---|---|---|
| 孙燕姿《遇见》音轨，46.60–105.10 秒 | 配乐 | YouTube Timeless Music 频道的官方 4K MV（`inputs/yujian/source.txt`），`yt-dlp` 取音轨 | 版权歌曲，没有授权；只在本机用，发布前要处理版权 |
| 歌词时间轴 | 字幕 | LRCLIB id 30558675 | LRCLIB 的公开数据；歌词本身的版权归词作者 |
| polar_fleece、curly_teddy_natural、terry_cloth、velour_velvet、wool_boucle、ribbed_corduroy、gingham_check、knitted_fleece、cotton_jersey | 布偶、手套、大衣、背板、布檐的布纹（颜色图只取明暗，再乘上自己的颜色；法线图直接用） | Poly Haven，1k JPG，`fetch_assets.py` 从 api.polyhaven.com 下载 | CC0 |
| blue_metal_plate | 机柜的旧烤漆（明暗、粗糙度、法线） | Poly Haven | CC0 |
| metal_plate | 爪子和镀铬件的粗糙度 | Poly Haven | CC0 |
| painted_metal_shutter | 下载了，没用上 | Poly Haven | CC0 |
| 13 个音效（clamp、latch、tick、thud、pat、cloth、glass、coin、ding、off、rocker、bulb、flap） | 爪子开合、落地、硬币、开关灯 | 本机 earshot 的音效库，`sfx_render` 合成 | 本机工具生成 |
| 马达声 | 小车和卷线 | `mix.py` 里用 numpy 合成 | 自己写的 |
| 字幕字体 宋体-简（Songti SC） | 歌词字幕，烧在画面里 | macOS 自带，`/System/Library/Fonts/Supplemental/Songti.ttc` | 系统字体，随 macOS 授权；公开发布前要确认能不能嵌进视频 |
| 玻璃上的灰、擦痕、指纹、手套印 | 玻璃的脏污贴图 | `make_tex.py` 用 numpy 画的 | 自己写的 |

没有用 `generate_3d`，没有用生成式的贴图，没有从 Sketchfab 或 Poly Pizza 下载模型。用 Blender 建模和渲染，全部由 Python 脚本驱动，没有手动操作（命令行 `blender -b` 运行）。所有模型（布偶、爪子、机器、手套）都是脚本里用球体、方块和管子搭的。

画风参考 `inputs/yujian/style-ref.jpg` 是 San-X 的角色图，只学了圆的形体、豆豆眼、缝线、纽扣和暖色旧纸的配色；七只布偶是自己设计的，没有照着其中任何一个角色做。

对标片《The Fable of Clawd》（Riley Brown，X 帖 2121642720045261185）只下载到 `/tmp` 抽帧看过，用来写差距对比，没有用它的任何画面或声音。
