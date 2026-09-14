# 可调参数面板与产物归属 · 网页线的交付加成

> 什么时候读：网页线的**收尾阶段**，以及任何**多文件项目**开始前。
> 前半（Tweaks）让用户不改代码就能看到可能性空间；后半（产物归属）让多文件项目不互相污染。

---

# 第一部分 · Tweaks：设计变体实时调参

## 一 · 何时加

| 情形 | 加不加 |
|---|---|
| 用户明说要「能调参」「多版本切换」 | ✅ 必须加 |
| 设计有多个变体需要对比 | ✅ 必须加 |
| 用户没提，但你判断几个 tweak 能帮用户看到可能性 | ✅ **也加** |

**默认推荐：每个 deck 加 2–3 个 tweak**（主题色 / 字号档 / 布局变体 / 动效开关）。
让用户看到可能性空间，本身就是设计服务的一部分——**不要等用户开口**。

## 二 · 实现：纯前端 localStorage（唯一推荐方案）

某些宿主环境靠 `postMessage` 把参数回写源码做持久化。本工作室统一用
**纯前端 localStorage** —— 效果一致（刷新后保留），但不依赖任何宿主能力，**在任何环境都能工作**。

**键名规范（必须遵守）**：所有键以 `rouo-deck-` 为前缀，tweak 再加 `tweak-`：

```
rouo-deck-tweak-theme        // 主题色变体
rouo-deck-tweak-type-scale   // 字号档
rouo-deck-tweak-layout       // 版式变体
rouo-deck-tweak-motion       // 动效开关
rouo-deck-low-power          // 低功耗（骨架已内建）
rouo-deck-note / -note-size  // 备注字号（骨架已内建）
rouo-deck-sync               // 观众屏同步（骨架已内建）
```

> ⚠️ 前缀是**硬约束**：改成别的前缀会与骨架内建的键冲突或漏读。

## 三 · 基本结构

```js
const TWEAK_DEFAULTS = {
  "tweak-theme": "ikb",        // 主题色变体
  "tweak-type-scale": 1,       // 字号档 0.9 / 1 / 1.1
  "tweak-motion": "on",        // on / off
};
const KEY = k => `rouo-deck-${k}`;

function readTweaks(){
  const out = { ...TWEAK_DEFAULTS };
  for (const k of Object.keys(TWEAK_DEFAULTS)) {
    const v = localStorage.getItem(KEY(k));
    if (v !== null) out[k] = JSON.parse(v);
  }
  return out;
}
function applyTweaks(t){
  const root = document.documentElement;
  root.dataset.tweakTheme = t["tweak-theme"];
  root.style.setProperty("--type-scale", t["tweak-type-scale"]);
  document.body.classList.toggle("low-power", t["tweak-motion"] === "off");
}
function setTweak(k, v){
  localStorage.setItem(KEY(k), JSON.stringify(v));
  applyTweaks(readTweaks());
  syncPanel();
}
```

**四个关键点**：

1. **默认值写死在 `TWEAK_DEFAULTS`**，不要让「没有 localStorage」变成「没有样式」
2. 应用方式优先用 `data-*` + CSS 变量，**不要**用 JS 逐个改元素样式（会和动效冲突）
3. 动效开关**直接复用骨架的 `low-power` 类**，不要另造一套开关
4. 面板本身是 UI，**不参与动效揭示**，并且要能被键盘操作

## 四 · 面板 UI 规范

| 项 | 要求 |
|---|---|
| 位置 | 右下角，默认**收起**为一个圆形小按钮 |
| 触达 | 展开后列出每个 tweak：名称 + 当前值 + 切换控件 |
| 样式 | 与 deck 同风格（用同一套 CSS 变量），不要引入第三方 UI 库 |
| 可访问性 | `Esc` 收起；控件可 Tab 到；有 `aria-label` |
| 打印/导出 | 导出 PDF / 截图前**自动隐藏面板**（加 `data-export-hide` 并在导出流程里设 `body.exporting`） |
| 与演讲者模式共存 | 演讲者模式面板优先；tweak 面板在演讲时收起并禁用 |

## 五 · 验证

- [ ] 刷新页面，所有 tweak 值保留
- [ ] 每个 tweak 单独切换，页面无异常、无控制台报错
- [ ] `tweak-motion = off` 时**页面依然完整可读**（不是「藏起来」）
- [ ] 导出 PDF/截图时面板不可见
- [ ] 清空 localStorage 后回到默认态，不白屏

---

# 第二部分 · 产物归属（多文件项目不互相污染）

## 六 · 一条硬规则

> **每个事实只有一个 owner。读它就去它的 owner 文件读，绝不把多个渠道合并成第二个真相。**

典型事故：页面文案在 A 文件、数据在 B 文件、又在 C 文件抄了一份数据「方便用」——
改了 A 没改 C，交付时两个版本都对不上。

## 七 · 归属矩阵（rouo 项目通用）

| 产物 | owner | 谁读它 | 禁止 |
|---|---|---|---|
| `facts.md` | **事实** | 所有写作环节 | 页面里出现未核验的事实；把推测写成断言 |
| `brand-kit.md` | **品牌资产** | 颜色/字体/logo 唯一来源 | 在页面里临时发明颜色 |
| `direction-choice.md` | **用户选择** | 风格族 + 方向 + 原话 | 事后改写成自己想要的措辞 |
| `design-brief.md` | **设计意图**（含画布、字号、页面队列） | 执笔环节 | 执笔时偏离 briefing 而不回改 |
| `design-lock.md` | **生产参数**（类名白名单、主题变量块、图片槽位、规格锁） | 执笔 + 校验 | 页面里自造类名/槽位 |
| `deck_data.json` | **量产线的页面内容** | `com_drive.py` | 在引擎脚本里硬编码内容 |
| `storyboard.md` | **视频分镜** | 视频导出环节 | 用时间表口头描述代替分镜卡 |
| `review-report.md` | **评审结论** | 用户 | 报表与真实发现不一致（P1 未清却写「全通过」） |
| `svg_output/*.svg` | **页面视觉** | 导出 | 用脚本批量生成 SVG（手作线铁律：逐页手写） |
| `assets/img/` | **图片素材** | 页面引用 | 页面里内联 base64 大图 |
| `exports/*` | **交付快照** | 用户 | 把 `exports/` 当编辑源（它是派生物，改了会丢） |

## 八 · 三条推论

1. **派生物过期就从源头重生成**，不要在派生物上手改（改了下次重建就没了）
2. **快照与源分离**：`exports/` 里的 PPTX/PDF 是快照；要改就改源（SVG / HTML / deck_data.json）
3. **同一个事实不要抄第二份**。确实需要冗余（如离线兜底），必须**标注来源与同步方式**

## 九 · 与 Gate 协议的衔接

总纲 §六 的 Gate 文件协议就是这张矩阵的运行形态：**文件不在 = 环节没做**。
本文件补的是「**文件之间不许互相打架**」——只检查存在性不够，还要检查**内容是否有唯一的 owner**。
