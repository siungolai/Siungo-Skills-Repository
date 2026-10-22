# 硬件事实速查（hardware-facts）

> 本文件是 `SKILL.md` §4、§5.1 的完整版：本机已实测的硬件事实，按「板子 / 引脚 / 编译配置 / WS2812 / 资源口径 / 工具链 / 依赖」组织。实测日期 2026-10-14，DHT11 一节 2026-10-15 复核。删掉本文件，`SKILL.md` §4 的速查表仍可执行，但会失去依据与出处。

---

## 一、板子

| 项 | 值 |
|---|---|
| 型号 | ESP32-S3-DevKitC-1 N16R8 |
| 芯片 revision | v0.2 |
| 晶体 | 40MHz |
| Flash | 16MB |
| PSRAM | 8MB OPI（`memory_type=qio_opi`） |
| USB | 板载原生 USB CDC（须 `-DARDUINO_USB_CDC_ON_BOOT=1`） |
| MAC | 见板子背面标签 | bringup 不用 MAC 做判据，故不记录 |
| VID:PID | 303A:1001 |
| 本机端口 | COM4 |
| IO 电平 | 3.3V（直短 GND/3V3 烧 IO） |
| PlatformIO board ID | `esp32-s3-devkitc-1` |

## 二、GPIO 边界

S3 共 45 个可用 GPIO（GPIO0–21 + GPIO26–48）。

| 脚 | 状态 | 依据 |
|---|---|---|
| GPIO1 / GPIO2 | I2C 禁接 | 实测全段 `endTransmission()` 返回 5（超时），`bus-probe` 读 `pullup=HIGH float=HIGH`（高阻态、外部无器件驱动或上拉）；换 GPIO4/5 立刻通 |
| GPIO19 / GPIO20 | 禁占 | 原生 USB D+/D-，占用即失板载串口下载 |
| GPIO4 / GPIO5 | 跑通的 I2C SCL / SDA | 实测 |
| GPIO7 | DHT11 DATA | 实测 |
| GPIO26–32 | 已占 | SPI0/1 封装内 Flash/PSRAM |
| GPIO33–37 | 已占 | 8 线 SPI 高位数据线（OPI PSRAM） |
| GPIO38 | 规划中 | 编码器按键，待 bringup |
| GPIO39–42 | 已占 | JTAG |
| GPIO43 / GPIO44 | 已占 | UART0 |
| GPIO48 | 板载 WS2812 数据脚 | 本机 v1.0 实测；v1.1 起官方取消 |

**驱动能力三档**：GPIO17/18 = 10mA、GPIO19/20 = 40mA、其余 20mA，累计 IO 输出上限 1500mA。数据手册未给每脚绝对最大电流；常见引用的「40mA」是 `PAD_DRIVER=3` 档典型源电流，不是绝对最大值。

## 三、platformio.ini 固定段

六个项目完全一致的板级段：

```ini
[env:esp32-s3-devkitc-1]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino
board_upload.flash_size = 16MB
board_build.arduino.memory_type = qio_opi
monitor_speed = 115200
build_flags =
    -DARDUINO_USB_CDC_ON_BOOT=1
```

- `uptime-oled` / `dht11-oled` / `clock-oled` / `lcd1602-uptime` 另加 `-Wall -Wextra`；`blink3` 不加。
- 换普通 8MB Flash 无 PSRAM 的 S3-DevKitC-1 时，去掉 `memory_type` 行。
- I2C 换脚只改 `src/main.cpp` 顶部的 `PIN_I2C_SCL` / `PIN_I2C_SDA` 常量——`Wire.begin(sda, scl, freq)` 可指定任意 GPIO，不动 `platformio.ini`。

## 四、板载 WS2812 与 LED 宏陷阱

**数据脚是 GPIO48**（`PIN_NEOPIXEL`），不是外接常见接法的 GPIO21。

**判定法（pin-probe）**：两段轮流打同一串颜色——第 1 段 GPIO21、第 2 段 GPIO48。

| 观测 | 结论 |
|---|---|
| 只第 2 段亮 | 板载数据脚在 48（本机实测，v1.0） |
| 只第 1 段亮 | 外接在 21 |
| 两段都不亮 | 板子没有板载 WS2812（v1.1 起官方取消）或灯损坏 |

**为什么不写 `LED_BUILTIN` / `RGB_BUILTIN`**：core 2.0.17 的 S3 变体里 `LED_BUILTIN = SOC_GPIO_PIN_COUNT + PIN_NEOPIXEL = 48 + 48 = 96`，且 `#define RGB_BUILTIN LED_BUILTIN`；hal 层 `esp32-hal-rgb-led.c` 里 `if (pin == RGB_BUILTIN) _pin = RGB_BUILTIN - SOC_GPIO_PIN_COUNT`（96−48=48 碰巧对）。这是在赌编译期常量等于芯片运行时常量，换变体即错位。本项目一律传字面量 48。

**外接三色共阳**：逐个 GPIO 输出 LOW 灯亮 = 共阳，输出 HIGH 灯亮 = 共阴。限流电阻 `(3.3V − Vf) ÷ 5mA`：红 220Ω、蓝绿 100Ω。先接线后上电。

## 五、资源占用口径

口径固定，否则跨项目数字不可比：

- **RAM** = `.dram0.data` + `.dram0.bss` ELF 段合计；
- **Flash** = `firmware.bin` 镜像总大小（含 image header、分区表与校验，故比 ELF 段合计略大）。

| 项目 | RAM | Flash |
|---|---|---|
| uptime-oled | 20,212 / 327,680（6.2%） | 282,973 / 3,342,336（8.5%） |
| lcd1602-uptime | 19,188（5.9%） | 282,469（8.5%） |
| dht11-oled | 20,268（6.2%） | 286,333（8.6%） |
| clock-oled | 46,144（14.1%） | 720,125（21.5%） |

`clock-oled` 的差异全部来自 libWiFi 协议栈（联网对时的必然代价），与 OLED 或时钟逻辑无关。除 `blink3` 外全部 `-Wall -Wextra` 零告警。

## 六、工具链版本

PlatformIO Core 6.2.0、Python 3.10.4、Windows 10、platform `espressif32` 7.1.3、framework-arduinoespressif32 `4.20017.260907+sha.dcc1105b`、toolchain-xtensa-esp32s3 `8.4.0+2021r2-patch5`、tool-esptoolpy `2.41100.260830`。

## 七、第三方依赖

`uptime-oled` / `clock-oled` / `dht11-oled` / `lcd1602-uptime` / `pin-probe` 零第三方依赖（只用 core 自带 `Wire` / `WiFi`，未引入 `NTPClient` / `ESP32Time`）。`blink3` 仅 `adafruit/Adafruit NeoPixel@^1.15.5`（实际 1.15.5，BSD-3-Clause），且仅 `ENABLE_ONBOARD_RGB=1` 板载模式需要；`NEO_GRB` 表示传输顺序 G,R,B 不是 R,G,B。

自写裸驱规模：OLED 约 200 行（1KB 显存 + 95 个 ASCII 5×7 字形 + 2 倍放大 + 分块传输）、1602 约 200 行（HD44780 4 位模式初始化序列 + PCF8574 影子寄存器 + 两个 nibble 合并进一次 I2C 事务）、DHT11 单头文件。

## 八、原始出处

- ESP32-S3 数据手册 v2.2：`espressif.com/documentation/esp32-s3_datasheet_en.pdf`
- TCA9548A 数据手册 SCPS207H：`ti.com/lit/ds/symlink/tca9548a.pdf`

两份提取件在 `.tmp-research/ESP32S3-FACTS.md` 与 `.tmp-research/TCA9548A-FACTS.md`，已被 `.gitignore` 排除不入库，是本文件 §2、§5.3 参数的依据。

## 九、本机沙箱边界

- `workspace-write` 下 `~/.platformio/platforms.lock` 写入被拒，编译需 `danger-full-access`。
- `pio device monitor` 不能在管道/重定向下用；读日志用 Python + pyserial 直读串口。
- PowerShell 管道按 GBK 解码外部输出，UTF-8 中文显示乱码（仅显示问题，不影响写入）。
