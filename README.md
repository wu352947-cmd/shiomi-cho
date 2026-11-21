# 汐見町 Shiomi-chō

一个可自由旋转的高精度 3D 日系动漫风海港小镇（治愈 / 夏日午后）。  
A freely rotatable 3D anime-style Japanese harbor-town diorama.

**在线查看：** https://wu352947-cmd.github.io/shiomi-cho/

拖动旋转，滚轮或双指缩放。手机可单指旋转、双指缩放。停止操作约 8 秒后会缓缓自动旋转。

## 操作

| 输入 | 作用 |
| --- | --- |
| 拖动 / 单指滑动 | 旋转镜头 |
| 滚轮 / 双指捏合 | 缩放 |
| 右键拖动 | 平移 |
| 底部按钮 | 跳到预设机位（全景 / 港口 / 商店街 / 神社 / 灯塔 / 踏切） |
| UI 开关 | 隐藏或显示界面 |

URL 参数：`?cam=overview\|harbor\|street\|shrine\|lighthouse\|crossing`，`?q=low\|med\|high`，`?ui=0`，`?auto=0`。

## 技术栈

- **Blender 5.2** 过程化建模（实心墙、嵌墙窗、日式屋顶、顶点 AO），导出 meshopt 压缩的 `town.glb`（约 21 MB，75 万三角面）。
- **Three.js 0.170** 网页查看器：三档赛璐珞着色、描边、新海诚式渐变天空与积云、风格化海面（浅滩/深海、泡沫、波光）、微风、bloom 与调色。
- 无需构建步骤，静态托管即可。相对路径，适合 GitHub Pages 子路径。

## 本地运行

```bash
npx --yes serve -p 8080 .
# 或: python3 -m http.server 8080
```

打开 http://127.0.0.1:8080/ 。重新生成模型：

```bash
blender -b --factory-startup --python blender/build.py
```

画风约定见 [ART_BIBLE.md](ART_BIBLE.md)，素材许可见 [CREDITS.md](CREDITS.md)。
