# SSD1306 驱动要点（ssd1306-driver-notes）

> `SKILL.md` §4.3、§4.5、§2.4 的完整版：SSD1306 128×64 I2C 的显存布局、初始化序列、事务分块、字模方向与两个字符扩展层。删掉本文件，主流程仍可执行，但会失去实现细节与依据。

---

## 一、基本参数

| 项 | 值 |
|---|---|
| 分辨率 | 128 × 64 |
| 接口 | I2C |
| 7 位地址 | **0x3C**（实测应答；丝印 0x78 是含读写位的 8 位写法）；少数 0x3D（丝印 0x7A） |
| 显存 | 1024 字节 = 128 列 × 8 页 |
| 字节语义 | **1 字节 = 1 列 8 个垂直像素，bit0 = 页内最上一行** |
| 页寻址 | `0x20, 0x02` |
| 速率 | 400kHz（诊断降到 100kHz） |
| 控制字节 | 0x00 = 命令流、0x40 = 显存数据流 |
| 供电 | VCC = 3V3 时必须开内部电荷泵 `0x8D, 0x14` |
| 本机接线 | SCL → GPIO4、SDA → GPIO5、VCC → 3V3、GND → GND |

**SCL 与 SDA 接反 = 完全不显示**，这是最常见的不亮原因，先量线序再怀疑别的。

**型号笔误**：首轮曾误记「SSD13159」，该型号不存在。SSD1315 是引脚与命令兼容的替代品，但本机确认是 SSD1306。

## 二、初始化序列（17 条）

```text
0xAE          关显示
0xD5 0x80     时钟分频
0xA8 0x3F     MUX 比 = 64
0xD3 0x00     显示偏移
0x40          起始行
0x8D 0x14     电荷泵（3.3V 必须开）
0x20 0x02     页寻址模式
0xA1          段重映射（左右镜像）
0xC8          行扫描反转
0xDA 0x12     引脚配置
0x81 0xCF     对比度
0xD9 0xF1     预充电周期
0xDB 0x40     复位电平
0xA4          输出跟随 RAM
0xA6          正常显示（非反色）
0x2E          停滚动
0xAF          开显示
```

## 三、setCursor 与事务分块

`setCursor(page, col)` 三条命令：

```text
0xB0 | (page & 0x07)              选页
0x00 | (col & 0x0F)               列低 4 位
0x10 | ((col >> 4) & 0x0F)        列高 4 位
```

每页 128 列，单次事务最多 `kChunkPayload = 64` 字节载荷（Wire 缓冲约 128 字节，含控制字节与地址字节余量），所以每页拆 2 次事务，一轮刷新 8 页 × 2 = **16 次事务**。

## 四、字模方向

**字模取模方向必须与显存一致**：1 字节 = 1 列 8 个垂直像素、bit0 = 页内最上一行。换字库不对齐会显示乱块——这不是接触不良，是取模方向错了。

`begin()` 内部自动调用 `fontDirProbe()`：画两条参照竖条停留 6000ms，供人工核对字模方向，并给串口判读指引。

## 五、驱动接口

```cpp
Ssd1306I2c(uint8_t scl, uint8_t sda, uint8_t addr = 0x3C, uint32_t hz = 400000);
```

| 方法 | 作用 |
|---|---|
| `begin()` | 初始化 `Wire`（含 `setTimeOut(50)`）并下发初始化序列，自动调 `fontDirProbe()` |
| `ready()` | 探测是否成功 |
| `flush()` | 刷全屏 16 次事务；**探测失败时直接返回** |
| `clear()` | 清显存 |
| `setCursor(page, col)` | 选页选列 |
| `fontDirProbe()` | 字模方向人工核对 |
| 底层 | `cmd` / `cmd2` / `probe` |

**常量**：`OLED_WIDTH=128`、`OLED_HEIGHT=64`、`OLED_PAGES=8`、`OLED_BUFFER_SIZE=1024`。

## 六、绘制接口：ASCII 版

`uptime-oled/src/ssd1306_i2c.h`：

| 方法 | 语义 |
|---|---|
| `drawChar5x7(x, page, c)` | 单字符 |
| `drawText5x7(x, page, s)` | 字符串 |
| `drawText5x7Scaled2x(x, page, s)` | 2 倍放大，字形高 14 像素跨 `page` 与 `page+1` 两页，步进 12 列 |
| `fillPageSpan(page, cols, bytes)` | 按列填充 |

**page 版行距只能取 8 的倍数**。

## 七、绘制接口：中文与任意 y 层

`clock-oled` 在 ASCII 版之上扩展，常量、构造函数、`begin()`/`flush()` 与 ASCII 版完全相同：

| 方法 | 语义 |
|---|---|
| `drawText5x7Y(x, y, s)` | 任意像素行定位 |
| `drawText5x7Scaled2xY(x, y, s)` | 2 倍放大 + 任意 y |
| `drawCnChar(x, y, codepoint)` | 单汉字（每汉字 16 列） |
| `drawCnCharY` | 单汉字 + 任意 y |
| `drawTextCn` / `drawTextCnY` | 中文字符串 |
| `cnTextWidth(s)` | 中文宽度（每汉字 16 列） |
| `drawBits(x, y, cols, n, rowsHeight)` | 位图；`rowsHeight` 取 8 或 16，取 16 时每列 2 字节**低字节在前**，跨页自动 OR，暗点不写，越界即停 |

字形缺失时画方框占位。y 版可任意像素行定位，page 版只能 8 的倍数。

**星期与月份用固定 ASCII 表**，避开 `strftime` 的 locale 依赖。

## 八、掉线保护（跨项目通用）

从机不在线时 `flush()` 每页 `endTransmission()` 阻塞到 50ms 超时，一轮刷新 ≈ 800ms，足以把 1 秒节拍带偏。因此 `flush()` 探测失败后**直接返回，不发任何事务**——计时精度与屏幕在线状态完全解耦。实测屏缺席仍 45 tick / 45 秒 = 1.0000 tick 每秒，无漂移。
