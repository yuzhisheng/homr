# homr jianpu_viewer

TypeScript Canvas 渲染器 — 用于高质量简谱预览。

从 jianpu-renderer 项目移植，作为 homr 简谱模块的可视化工具。

## 功能

- HTML5 Canvas 渲染（53 个 SVG 路径符号）
- 支持加载 `.jtokens` 文件（通过 `jtokens_loader.ts` 转换为内部 JSON 格式）
- 支持加载 jianpu-renderer JSON 格式
- 暗/亮双主题
- 缩放、间距调节
- PNG 导出
- Monaco JSON 编辑器

## 使用

```bash
cd homr/jianpu_viewer
npm install
npm run dev
```

然后在浏览器中打开 Vite 开发服务器地址。

## 文件结构

```
jianpu_viewer/
├── src/
│   ├── jtokens_loader.ts    # .jtokens → Score JSON 转换器
│   ├── App.tsx              # 主应用
│   ├── types/               # TypeScript 类型定义
│   ├── engine/              # 布局引擎 + 渲染器 + 符号库
│   ├── components/          # React 组件
│   ├── data/                # 示例乐谱
│   └── schema/              # JSON Schema
├── scripts/                 # 训练数据生成脚本
├── res/                     # 符号图标资源
└── package.json
```

## 与 homr Python 模块的关系

- Python `homr/jianpu/svg_renderer.py` — 用于流程内联 SVG 渲染（训练数据生成）
- TypeScript `jianpu_viewer/` — 用于高质量交互式预览
- 两者使用相同的布局算法和符号库
- `.jtokens` 文件可通过 `jtokens_loader.ts` 在 TypeScript 端加载
