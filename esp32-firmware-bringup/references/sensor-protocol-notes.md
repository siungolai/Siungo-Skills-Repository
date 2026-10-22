# 传感器协议要点（sensor-protocol-notes）

> `SKILL.md` §5.5、§2.4 的完整版：DHT11 时序自写驱动的完整接口、位判决自校准原理、错误码与物理故障的对应，以及弃用 Adafruit DHT 库的两个硬原因。删掉本文件，主流程仍可执行，但会失去协议细节与弃用依据。

---

## 一、DHT11 基本参数

| 项 | 值 |
|---|---|
| 温度 | 0–50°C ±2°C |
| 湿度 | 20–90%RH ±5%RH |
| 分辨率 | 1°C / 1%RH，**只有整数没有小数**（`data[1]`/`data[3]` 小数位恒 0；DHT22 才有小数） |
| 采样率上限 | 1Hz |
| 总线 | 单总线开漏 + 上拉 |
| 本机接线 | DATA → GPIO7、VCC → 3V3、GND → GND |
| 上拉 | 模块板自带 4.7k~10k，**不需外接**（裸传感器才要补） |
| 供电 | 3.3V（模块板 3.3–5V 均可） |

**0–50°C / 20–90%RH 是驱动接受范围，即精度保证范围，不是器件物理极限**。驱动常量 `DHT11_TEMP_MIN` / `DHT11_TEMP_MAX` / `DHT11_HUM_MIN` / `DHT11_HUM_MAX` 取这四个值，超出即判 `DHT_ERR_RANGE`——跑出区间按 OUT OF RANGE 报错，而不是当成正常读数。

**带灯模块的灯由模块 VCC 供电恒亮，不表示读到数据**。判断程序在不在，看屏幕上每秒 +1 的刷新计数。

## 二、接口（`dht11-oled/src/dht11.h`，零第三方依赖）

```cpp
enum DhtStatus : uint8_t {
  DHT_OK = 0, DHT_ERR_NO_RESPONSE, DHT_ERR_TIMEOUT,
  DHT_ERR_CHECKSUM, DHT_ERR_RANGE
};

struct DhtReading {
  float temperature; float humidity;
  bool tempValid; bool humValid;
  uint8_t status; uint32_t atMs;
};

bool dht11Read(uint8_t pin, DhtReading& out);
bool dhtDataLineLooksAlive(uint8_t pin, bool* externallyPulled);
size_t formatDhtCsv(uint32_t sec, const DhtReading& r,
                    uint32_t failCount, char* out, size_t outLen);
const char* dhtStatusText(uint8_t status);
```

- **`dht11Read` 一次传输解出 5 字节 40 位，不做节流**——节流是调用方职责。这是它与 Adafruit 库的关键分野。
- **`dhtDataLineLooksAlive`**：先 `INPUT_PULLUP` 读一次，再纯 `INPUT` 读一次；外部读到 HIGH 才证明上拉存在。
- **`formatDhtCsv`**：输出 `t=%lus,hum=%s,temp=%s,ok=%u,fail=%lu`，无效字段写 `--` 不写 0（0°C 是合法读数，写 0 就跟没读到混在一起）。
- **`dhtStatusText`**：`OK / NO RESPONSE / TIMEOUT / BAD CHECKSUM / OUT OF RANGE / UNKNOWN`。

**错误码对应四种物理故障**（显示在第 7 页，接错线不用连串口就知道）：

| 状态 | 物理含义 |
|---|---|
| `DHT_ERR_NO_RESPONSE` | 发了起始信号没拉低应答——器件没接上或没供电 |
| `DHT_ERR_TIMEOUT` | 应答到了但某位电平等不到边沿——接触/线长问题 |
| `DHT_ERR_CHECKSUM` | 40 位收齐但校验和不对——多半时序抖动 |
| `DHT_ERR_RANGE` | 校验和过但数值超量程——元件坏了 |

## 三、时序

```text
起始   digitalWrite(pin, LOW); delay(20);      // 手册 ≥18ms
应答   等低 / 等高，各循环上限 cyclesPerUs*100   // 手册各 80µs
收 40 位 noInterrupts() 期间逐位测宽
       每位低电平 50µs，高电平 26–28µs(0) / 70µs(1)
       每位低、高各有循环上限
结束   50µs 低后释放总线
```

每个等待循环都有 cycle 上限，任何一步超时立刻返回错误码——**不可能自旋到看门狗**。

校验和 `data[0]+data[1]+data[2]+data[3] == data[4]`；解码 `humidity=data[0]`、`temperature=data[2]`。

## 四、位判决必须自校准

**错误做法**：拿「名义 50µs × cyclesPerUs」当阈值。

**原因**：`digitalRead()` 不是一条指令，循环体有开销，实测循环数被放大。用绝对阈值比任何真实读数都大，结果是 **40 位全判 0**。

**正确做法**——比较本位自己的高低电平实测宽度：

```cpp
if (highCycles > lowCycles) bit = 1;
```

| 位 | 低电平 | 高电平 | 判据 |
|---|---|---|---|
| 0 | ~50µs | ~26µs | 高 < 低 |
| 1 | ~50µs | ~70µs | 高 > 低 |

两个量在同一环境实测，循环开销同时放大、**比较时抵消**，与 CPU 主频无关。这是自校准判决：比的是相对宽度，不是绝对时长。

## 五、弃用 Adafruit DHT sensor library 的两个硬原因

**原因一：背靠背连调撞冷却期。** 库把原始字节 `data[5]` 设 private，没有「读一次拿温湿度两个值」的接口，调用方只能背靠背 `readHumidity()` + `readTemperature()`，各自触发一次完整传输。DHT11 两次转换间要求 ≥1s，同秒连调第二次校验和不过返回 NAN → 屏幕 `--`。实机症状正是**湿度正常、温度恒 `--`**——湿度先读拿到有效值，温度后读撞冷却期。

**原因二：传感器不在线时关中断自旋。** `expectPulse()` 里 `while (digitalRead(_pin) == level) {}` 且中断已关，传感器不在线时自旋到看门狗整板重启：

```text
Guru Meditation Error: Core 1 panic'ed (Interrupt wdt timeout on CPU1)
```

反复重启，连「传感器没接」的诊断都来不及打印。

**自写的价值**：一次传输解出全部 5 字节（无冷却期问题）+ 每个等待循环有 cycle 上限（不可能自旋到看门狗）。两条硬伤同时消失。

## 六、采样节拍常量

```cpp
constexpr uint32_t TICK_MS        = 1000;   // 屏幕刷新节拍
constexpr uint32_t SAMPLE_MS      = 1000;   // 贴 DHT11 物理上限
constexpr uint32_t RETRY_MS       = 2000;   // 连续失败往往是接触问题，密采样只让日志刷屏
constexpr uint32_t DHT_WARMUP_MS  = 1500;   // 上电先空转等供电稳
constexpr uint32_t OLED_RETRY_MS  = 5000;   // 屏幕掉线自愈，接线插好不必重新上电
```

失败重试节拍：

```cpp
uint32_t period = hasReading ? SAMPLE_MS
                : ((now < DHT_WARMUP_MS) ? UINT32_MAX : RETRY_MS);
```

上电第一个 tick 是 no-data 属正常。实测 20 秒 19 次采样零失败；对传感器呼吸，湿度 79%→43%、温度 33→32°C，证明读的是真实传感器而非缓存。

## 七、串口日志两类行

**分开两类，别混：**

- `[tick N]`：每个屏幕刷新节拍打一次，报当前读数状态、年龄与累计失败。
- `t=Ns,...`：每次采样打一次（成功失败都打），固定字段 CSV，`grep -c 'ok=1'` 直接统计成功率。

日志刻意用 ASCII 不用中文：UTF-8 到部分串口工具变乱码，而故障信息恰是唯一线索。
