---
name: chanlun
description: 基于缠论（缠中说禅）的形态识别引擎，使用czsc库自动检测K线分型、笔、中枢，并生成一买/一卖/二买/二卖/三买/三卖等买卖点信号。支持多周期分析和形态分类（3/5/7/9/11笔形态）。
category: strategy
---
# 缠论形态识别

## 用途

基于**缠中说禅**理论的价格形态识别。缠论是一套完全基于价格结构的技术分析方法，核心链路：

```
原始K线 → 去包含处理 → 分型识别 → 笔检测 → 中枢构建 → 买卖点判定
```

适用于任何有 OHLCV 数据的市场（A股、加密货币、期货等）。

## 核心概念

| 概念 | 说明 | 详细文档 |
| --- | --- | --- |
| 分型（FX） | 顶分型：中间K线最高；底分型：中间K线最低 | [分型](references/核心概念/分型.md) |
| 笔（BI） | 相邻顶底分型之间的一段走势，最小单元 | [笔](references/核心概念/笔.md) |
| 中枢（ZS） | 至少3笔构成的价格重叠区域，趋势的核心 | [中枢](references/核心概念/中枢.md) |

## 买卖点体系

| 买卖点 | 含义 | 详细文档 |
| --- | --- | --- |
| 一买/一卖 | 趋势结束后的第一个反转信号（背驰点） | [一买一卖](references/买卖点/一买一卖.md) |
| 二买/二卖 | 一买/一卖后回调不破底/顶的确认信号 | [二买二卖](references/买卖点/二买二卖.md) |
| 三买/三卖 | 中枢上移/下移后回调不进入前中枢的信号 | [三买三卖](references/买卖点/三买三卖.md) |

## 依赖安装

```bash
pip install "czsc @ git+https://github.com/waditu/czsc@1.0.0-rc.8" requests pandas
```

在 `1.0.0-rc.8` 版本中，核心对象建议直接从 `czsc` 顶层导入（例如 `RawBar/Freq/Direction/BI/FX/ZS`），不要使用 `czsc.objects` 这类旧路径。

## 快速上手

```python
from czsc import CZSC, RawBar, Freq
from czsc.signals import cxt
from datetime import datetime

# 准备 RawBar 列表（需按时间正序排列）
bars = [
    RawBar(symbol="BTC-USDT", id=0, dt=datetime(2026,1,1),
           freq=Freq.D, open=70000, close=71000,
           high=72000, low=69000, vol=1000, amount=71000000),
    # ... 更多K线
]

# 创建分析器（参数签名：CZSC(bars_raw, max_bi_num=50)）
c = CZSC(bars)

# 调用信号函数（按需组合）
signals = {}
signals.update(cxt.cxt_first_buy_V221126(c, di=1))
signals.update(cxt.cxt_first_sell_V221126(c, di=1))
signals.update(cxt.cxt_three_bi_V230618(c, di=1))
signals.update(cxt.cxt_five_bi_V230619(c, di=1))
print(signals)

# 访问结构结果
print(c.bi_list)    # 已完成的笔
print(c.bars_ubi)   # 未完成笔中的K线
```

## 可用信号函数（czsc.signals.cxt）

`czsc.signals.cxt` 模块提供缠论相关信号函数。你可以用下面代码在本地直接枚举（避免文档与安装版本不一致）：

```python
import importlib

cxt = importlib.import_module("czsc.signals.cxt")
names = sorted(n for n in dir(cxt) if n.startswith("cxt_") and callable(getattr(cxt, n)))
print("\n".join(names))
```

以下为 `1.0.0-rc.8` 在本项目 `.venv` 环境中实际可用的函数名（共 43 个）：

| 函数 |
| --- |
| `cxt_bi_base_V230228` |
| `cxt_bi_end_V230104` |
| `cxt_bi_end_V230105` |
| `cxt_bi_end_V230222` |
| `cxt_bi_end_V230224` |
| `cxt_bi_end_V230312` |
| `cxt_bi_end_V230320` |
| `cxt_bi_end_V230322` |
| `cxt_bi_end_V230324` |
| `cxt_bi_end_V230618` |
| `cxt_bi_end_V230815` |
| `cxt_bi_status_V230101` |
| `cxt_bi_status_V230102` |
| `cxt_bi_stop_V230815` |
| `cxt_bi_trend_V230824` |
| `cxt_bi_trend_V230913` |
| `cxt_bi_zdf_V230601` |
| `cxt_bs_V240526` |
| `cxt_bs_V240527` |
| `cxt_decision_V240526` |
| `cxt_decision_V240612` |
| `cxt_decision_V240613` |
| `cxt_decision_V240614` |
| `cxt_double_zs_V230311` |
| `cxt_eleven_bi_V230622` |
| `cxt_first_buy_V221126` |
| `cxt_first_sell_V221126` |
| `cxt_five_bi_V230619` |
| `cxt_fx_power_V221107` |
| `cxt_intraday_V230701` |
| `cxt_nine_bi_V230621` |
| `cxt_overlap_V240526` |
| `cxt_overlap_V240612` |
| `cxt_range_oscillation_V230620` |
| `cxt_second_bs_V230320` |
| `cxt_second_bs_V240524` |
| `cxt_seven_bi_V230620` |
| `cxt_third_bs_V230318` |
| `cxt_third_bs_V230319` |
| `cxt_third_buy_V230228` |
| `cxt_three_bi_V230618` |
| `cxt_ubi_end_V230816` |
| `cxt_zhong_shu_gong_zhen_V221221` |

## 信号约定

### 输入对象

- 单周期信号：参数是 `c: CZSC`，适用于本 skill 的 `SignalEngine`。
- 多周期信号：参数是 `cat: CzscSignals`，需要先构建多周期容器（包含多个周期的 CZSC 实例）。`cxt_intraday_V230701`、`cxt_zhong_shu_gong_zhen_V221221` 属于这一类。

### 输出结构（如何判定触发）

- 每个 cxt 信号函数返回 `OrderedDict[str, str]`（通常只有 1 个键值对，可以直接 `signals.update(...)` 合并）。
- key 一般由 “参数模板” 决定（包含周期、di、指标参数等），例如 `日线_D1B_BUY1`。
- value 通常是 `"{v1}_{v2}_{v3}_{score}"`：
  - `v1`：核心状态字段；`其他` 表示未触发
  - `v2/v3`：辅助解释字段（例如 `5笔`、`均线新高`、`任意`）
  - `score`：一般为 `0`（更多是信号系统兼容字段，本 skill 默认不使用）
- 推荐解析方式：
  - `v1 = value.split('_', 1)[0]`
  - “是否触发”：`v1 != "其他"`

### 通用 kwargs（不同函数含义不同）

| 参数 | 常见含义 | 常见默认值 |
| --- | --- | --- |
| `di` | 倒数第 `di` 个（笔 / 分型 / 日） | `1` |
| `bi_init_length` | 笔状态判断阈值（小于该值更偏“转折”，否则偏“中继”） | `9` |
| `timeperiod` | 均线周期 | `21/34/5`（因函数而异） |
| `ma_type` | 均线类型（如 `SMA`） | `SMA` |
| `fastperiod/slowperiod/signalperiod` | MACD 参数 | `12/26/9` |
| `th` | 阈值（止损距离 bp / 震荡振幅阈值 % / 均线穿越阈值等） | `2/50`（因函数而异） |
| `max_overlap` | 顶底分型重叠容忍次数等 | `3` |
| `n/w/t` | 窗口或数量参数（n=数量，w=窗口，t=重合次数） | `n=4/7/9` 等 |

### 函数说明（rc.8 实测）

| 函数 | 输入 | kwargs | 参数模板 | 说明 |
| --- | --- | --- | --- | --- |
| `cxt_bi_base_V230228` | `c` | `bi_init_length` | `"{freq}_D0BL{bi_init_length}_V230228"` | BI基础信号 |
| `cxt_bi_end_V230104` | `c` | `ma_type, timeperiod` | `"{freq}_D0{ma_type}#{timeperiod}T{th}_BE辅助V230104"` | 单均线辅助判断笔结束 |
| `cxt_bi_end_V230105` | `c` | `ma_type, th, timeperiod` | `"{freq}_D0{ma_type}#{timeperiod}T{th}_BE辅助V230105"` | K线形态+均线辅助判断笔结束 |
| `cxt_bi_end_V230222` | `c` | `max_overlap` | `"{freq}_D1MO{max_overlap}_BE辅助V230222"` | 当前是最后笔的第几次新低底分型或新高顶分型，用于笔结束辅助 |
| `cxt_bi_end_V230224` | `c` | `-` | `"{freq}_D1_BE辅助V230224"` | 量价配合的笔结束辅助 |
| `cxt_bi_end_V230312` | `c` | `fastperiod, signalperiod, slowperiod` | `"{freq}_D0MACD{fastperiod}#{slowperiod}#{signalperiod}_BE辅助V230312"` | MACD辅助判断笔结束信号 |
| `cxt_bi_end_V230320` | `c` | `max_overlap` | `"{freq}_D0质数窗口MO{max_overlap}_BE辅助V230320"` | 100以内质数时序窗口辅助笔结束判断 |
| `cxt_bi_end_V230322` | `c` | `ma_type, timeperiod` | `"{freq}_D0分型配合{ma_type}#{timeperiod}_BE辅助V230322"` | 分型配合均线辅助判断笔的结束 |
| `cxt_bi_end_V230324` | `c` | `ma_type, timeperiod` | `"{freq}_D0{ma_type}#{timeperiod}均线突破_BE辅助V230324"` | 笔结束分型的均线突破判断笔的结束 |
| `cxt_bi_end_V230618` | `c` | `di, max_overlap` | `"{freq}_D{di}MO{max_overlap}_BE辅助V230618"` | 笔结束辅助判断 |
| `cxt_bi_end_V230815` | `c` | `-` | `"{freq}_快速突破_BE辅助V230815"` | 一两根K线快速突破反向笔 |
| `cxt_bi_status_V230101` | `c` | `-` | `"{freq}_D1_表里关系V230101"` | 笔的表里关系 |
| `cxt_bi_status_V230102` | `c` | `-` | `"{freq}_D1_表里关系V230102"` | 笔的表里关系 |
| `cxt_bi_stop_V230815` | `c` | `th` | `"{freq}_距离{th}BP_止损V230815"` | 定位笔的止损距离大小 |
| `cxt_bi_trend_V230824` | `c` | `di, n, th` | `"{freq}_D{di}N{n}TH{th}_形态V230824"` | 判断N笔形态 |
| `cxt_bi_trend_V230913` | `c` | `di, n` | `"{freq}_D{di}N{n}笔趋势_高低点辅助判断V230913"` | 辅助判断股票通道信号 |
| `cxt_bi_zdf_V230601` | `c` | `di, n` | `"{freq}_D{di}N{n}_分层V230601"` | BI涨跌幅的分层判断 |
| `cxt_bs_V240526` | `c` | `-` | `"{freq}_趋势跟随_BS辅助V240526"` | 快速走势之后的减速反弹，形成第反弹买点 |
| `cxt_bs_V240527` | `c` | `-` | `"{freq}_趋势跟随_BS辅助V240527"` | 快速走势之后的减速反弹，形成第反弹买点 |
| `cxt_decision_V240526` | `c` | `n` | `"{freq}_分型区域N{n}_决策区域V240526"` | 根据最后一根K线与最后一笔的分型区间，构建交易决策区域 |
| `cxt_decision_V240612` | `c` | `n, w` | `"{freq}_W{w}N{n}高低点_决策区域V240612"` | 以最近W根K线的高低点附近N个价位作为决策区域 |
| `cxt_decision_V240613` | `c` | `n` | `"{freq}_放量笔N{n}BS2_决策区域V240613"` | 取最近N笔：向下未新低且累计量最大则开多；向上未新高且累计量最大则开空 |
| `cxt_decision_V240614` | `c` | `n` | `"{freq}_放量笔N{n}_决策区域V240614"` | 取最近N笔：向下新低且累计量最大则开多；向上新高且累计量最大则开空 |
| `cxt_double_zs_V230311` | `c` | `di` | `"{freq}_D{di}双中枢_BS1辅助V230311"` | 两个中枢组合辅助判断BS1 |
| `cxt_eleven_bi_V230622` | `c` | `di` | `"{freq}_D{di}十一笔_形态V230622"` | 十一笔形态分类 |
| `cxt_first_buy_V221126` | `c` | `di` | `"{freq}_D{di}B_BUY1"` | 一买信号 |
| `cxt_first_sell_V221126` | `c` | `di` | `"{freq}_D{di}B_SELL1"` | 一卖信号 |
| `cxt_five_bi_V230619` | `c` | `di` | `"{freq}_D{di}五笔_形态V230619"` | 五笔形态分类 |
| `cxt_fx_power_V221107` | `c` | `di` | `"{freq}_D{di}F_分型强弱"` | 倒数第di个分型的强弱 |
| `cxt_intraday_V230701` | `cat` | `di, freq1, freq2` | `"{freq1}#{freq2}_D{di}日_走势分类V230701"` | 每日走势分类 |
| `cxt_nine_bi_V230621` | `c` | `di` | `"{freq}_D{di}九笔_形态V230621"` | 九笔形态分类 |
| `cxt_overlap_V240526` | `c` | `-` | `"{freq}_顶底重合_支撑压力V240526"` | 收盘价与最近9笔顶底分型重合次数 |
| `cxt_overlap_V240612` | `c` | `n` | `"{freq}_SNR顺畅N{n}_支撑压力V240612"` | 顺畅笔的顶底分型构建支撑压力位 |
| `cxt_range_oscillation_V230620` | `c` | `di, th` | `"{freq}_D{di}TH{th}_区间震荡V230620"` | 判断区间震荡 |
| `cxt_second_bs_V230320` | `c` | `di, ma_type, timeperiod` | `"{freq}_D{di}#{ma_type}#{timeperiod}_BS2辅助V230320"` | 均线辅助识别第二类买卖点 |
| `cxt_second_bs_V240524` | `c` | `di, t, w` | `"{freq}_D{di}W{w}T{t}_第二买卖点V240524"` | 中枢视角下的并列二买 |
| `cxt_seven_bi_V230620` | `c` | `di` | `"{freq}_D{di}七笔_形态V230620"` | 七笔形态分类 |
| `cxt_third_bs_V230318` | `c` | `di, ma_type, timeperiod` | `"{freq}_D{di}#{ma_type}#{timeperiod}_BS3辅助V230318"` | 均线辅助识别第三类买卖点（已标记 deprecated） |
| `cxt_third_bs_V230319` | `c` | `di, ma_type, timeperiod` | `"{freq}_D{di}#{ma_type}#{timeperiod}_BS3辅助V230319"` | 均线辅助识别第三类买卖点（推荐） |
| `cxt_third_buy_V230228` | `c` | `di` | `"{freq}_D{di}_三买辅助V230228"` | 笔三买辅助 |
| `cxt_three_bi_V230618` | `c` | `di` | `"{freq}_D{di}三笔_形态V230618"` | 三笔形态分类 |
| `cxt_ubi_end_V230816` | `c` | `-` | `"{freq}_UBI_BE辅助V230816"` | 未完成笔的新低/新高次数，用于笔结束辅助 |
| `cxt_zhong_shu_gong_zhen_V221221` | `cat` | `-` | `"{freq1}_{freq2}_中枢共振V221221"` | 大小级别中枢共振（类二买共振） |

### 本 skill 默认用到的核心信号（建议如何用）

| 信号 | 关注字段 | 触发判断（建议） | 备注 |
| --- | --- | --- | --- |
| `cxt_first_buy_V221126` | `v1/v2` | `v1 == "一买"` | `v2` 常带 `{N}笔`，可以作为过滤条件（例如只接受 `>= 9笔`） |
| `cxt_first_sell_V221126` | `v1/v2` | `v1 == "一卖"` | 同上 |
| `cxt_three_bi_V230618` | `v1` | `v1 in {"向上盘背","向下盘背"}` | 还会输出 `向上/向下` 的 `奔走型/收敛/扩张/不重合/无背` 等形态 |
| `cxt_five_bi_V230619` | `v1` | 多头：`v1 in {"aAb式底背驰","类趋势底背驰","上颈线突破","类三买"}`；空头：`v1 in {"aAb式顶背驰","类趋势顶背驰","下颈线突破","类三卖"}` | 五笔形态更偏“形态分型”，通常适合当过滤器/加分项 |
| `cxt_bi_base_V230228` | `v1/v2` | 多头（辅助）：`v1=="向下" and v2=="转折"`；空头（辅助）：`v1=="向上" and v2=="转折"` | 这个信号输出的是“当前笔的方向 & 状态（中继/转折）” |

## signal_engine.py 生成规范（必须遵守）

- `generate(self, data_map)` 的 `data_map` value 必须是 `pd.DataFrame`，不能是 `dict`；否则会触发 `.iloc` 报错。
- `CZSC` 只接受 `List[RawBar]`，不能把 `dict` 当 bar 传入；否则会触发 `cannot be converted to 'RawBar'`。
- cxt 信号函数返回的是 `OrderedDict[str, str]`，不是带 `.v1` 属性的对象；必须从 value 里解析 `v1`。
- 不允许在 `signal_engine.py` 顶层执行网络请求/回测逻辑；只能定义函数、类、常量（runner 会做 AST 安全校验）。

### 三类买卖点模板（用于生成 code/signal_engine.py）

```python
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Tuple, Union

import pandas as pd
from czsc import CZSC, Freq, RawBar
from czsc.signals import cxt


def _df_to_bars(df: pd.DataFrame, symbol: str, freq: Union[str, Freq] = "D") -> list[RawBar]:
    if isinstance(freq, str):
        freq = getattr(Freq, freq)
    bars: list[RawBar] = []
    for i, (dt, row) in enumerate(df.iterrows()):
        if not isinstance(dt, datetime):
            dt = pd.Timestamp(dt).to_pydatetime()
        bars.append(RawBar(
            symbol=symbol,
            id=i,
            dt=dt,
            freq=freq,
            open=float(row["open"]),
            close=float(row["close"]),
            high=float(row["high"]),
            low=float(row["low"]),
            vol=float(row.get("volume", row.get("vol", 0))),
            amount=float(row.get("amount", 0)),
        ))
    return bars


def _odict_v1(sig: Any) -> str:
    if not sig:
        return "其他"
    if isinstance(sig, dict):
        val = next(iter(sig.values()), "")
    else:
        val = sig
    s = str(val)
    return s.split("_", 1)[0] if s else "其他"


class SignalEngine:
    def __init__(self, freq: Union[str, Freq] = "D"):
        self.freq = freq
        self.ma_type = "SMA"
        self.ma_period_bs2 = 21
        self.ma_period_bs3 = 34

    def interpret_signal(self, signals: Dict[str, str]) -> Tuple[int, str]:
        buy_signals = []
        sell_signals = []

        if signals.get("first_buy") == "一买":
            buy_signals.append("一买")
        if signals.get("first_sell") == "一卖":
            sell_signals.append("一卖")
        if signals.get("second_bs") == "二买":
            buy_signals.append("二买")
        elif signals.get("second_bs") == "二卖":
            sell_signals.append("二卖")
        if signals.get("third_bs") == "三买":
            buy_signals.append("三买")
        elif signals.get("third_bs") == "三卖":
            sell_signals.append("三卖")

        if buy_signals and not sell_signals:
            priority = {"一买": 1, "二买": 2, "三买": 3}
            best_buy = min(buy_signals, key=lambda x: priority.get(x, 99))
            return 1, best_buy
        if sell_signals and not buy_signals:
            priority = {"一卖": 1, "二卖": 2, "三卖": 3}
            best_sell = min(sell_signals, key=lambda x: priority.get(x, 99))
            return -1, best_sell
        return 0, "无信号"

    def get_chanlun_signals(self, c: CZSC) -> Dict[str, str]:
        if len(c.bi_list) < 6:
            return {}
        return {
            "first_buy": _odict_v1(cxt.cxt_first_buy_V221126(c, di=1)),
            "first_sell": _odict_v1(cxt.cxt_first_sell_V221126(c, di=1)),
            "second_bs": _odict_v1(cxt.cxt_second_bs_V230320(
                c, di=1, ma_type=self.ma_type, timeperiod=self.ma_period_bs2
            )),
            "third_bs": _odict_v1(cxt.cxt_third_bs_V230319(
                c, di=1, ma_type=self.ma_type, timeperiod=self.ma_period_bs3
            )),
        }

    def generate(self, data_map: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        result: Dict[str, pd.Series] = {}
        for code, df in data_map.items():
            if not isinstance(df, pd.DataFrame):
                raise TypeError(f"data_map[{code!r}] must be a pandas DataFrame, got {type(df).__name__}")
            df = df.sort_index()
            signal = pd.Series(0, index=df.index)

            bars = _df_to_bars(df, code, self.freq)
            if len(bars) < 80:
                result[code] = signal
                continue

            c = CZSC(bars[:50])
            for bar in bars[50:]:
                c.update(bar)
                action, _reason = self.interpret_signal(self.get_chanlun_signals(c))
                if action != 0:
                    signal.iloc[bar.id] = action

            result[code] = signal
        return result
```

## 数据格式

czsc 接受 `List[RawBar]`，每个 RawBar 包含：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| symbol | str | 标的代码 |
| id | int | 序号（从0开始） |
| dt | datetime | 时间 |
| freq | Freq | 频率：`Freq.F1/F5/F15/F30/F60/D/W/M` |
| open | float | 开盘价 |
| close | float | 收盘价 |
| high | float | 最高价 |
| low | float | 最低价 |
| vol | float | 成交量 |
| amount | float | 成交额 |

## 实现方式

使用 [czsc](https://github.com/waditu/czsc) 库（Release `1.0.0-rc.8`），核心分析引擎由 Rust 扩展提供，Python 层负责信号组合与数据接口。支持增量更新，适合实时分析。
