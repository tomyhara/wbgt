# WBGT熱中症警戒キオスク端末

Raspberry Piを使用した熱中症警戒アラート情報と天気予報を表示するキオスク端末システムです。

## ✨ 機能

- 🌤️ **リアルタイム天気情報** - 気象庁APIから取得
- 🌡️ **WBGT指数自動計算** - 湿球黒球温度による熱中症リスク判定
- 🚨 **熱中症警戒アラート** - 今日・明日の警戒レベル表示
- 🎨 **色分け表示** - 危険度に応じた視覚的な警告
- 🔄 **自動更新** - 30分間隔でのデータ更新
- 🖥️ **ターミナル版** - 安定動作、低負荷
- 🪟 **GUI版** - 実験的サポート

## 🛠️ 必要な環境

- Raspberry Pi 3以上（推奨：Raspberry Pi 4）
- Python 3.8以上
- インターネット接続
- ディスプレイ（オプション：タッチスクリーン）

## 🚀 クイックスタート

### 1. セットアップ
```bash
# リポジトリをクローン
git clone <repository-url>
cd wbgt

# 自動セットアップ実行
chmod +x install.sh
./install.sh
```

### 2. 設定
```bash
# 設定ファイルを編集（地域を変更する場合）
nano config.py
```

### 3. 実行

**デモモード（動作確認用）：**
```bash
python3 wbgt_kiosk.py --demo
```

**通常モード（本格運用）：**
```bash
python3 wbgt_kiosk.py
```

**GUI版（実験的）：**
```bash
python3 wbgt_kiosk.py --gui
```

## 📱 使用方法

### コマンドオプション
```bash
python3 wbgt_kiosk.py           # ターミナル版（推奨）
python3 wbgt_kiosk.py --demo    # デモモード（3回更新で終了）
python3 wbgt_kiosk.py --gui     # GUI版（実験的）
python3 wbgt_kiosk.py --help    # ヘルプ表示
```

### 操作方法
- **Ctrl+C**: アプリケーション終了
- **自動更新**: 30分間隔（デモモードは5秒間隔）

## 🗾 地域設定

`config.py`で日本全国の主要都市に対応：

```python
# 東京（デフォルト）
AREA_CODE = "130000"
CITY_NAME = "東京"

# その他の例
AREA_CODE = "270000"  # 大阪
AREA_CODE = "230000"  # 名古屋
AREA_CODE = "400000"  # 福岡
```

## 🔧 自動起動設定

### systemd使用（推奨）
```bash
sudo nano /etc/systemd/system/wbgt-kiosk.service
```

```ini
[Unit]
Description=WBGT Heat Stroke Warning Kiosk
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wbgt
ExecStart=/usr/bin/python3 /home/pi/wbgt/wbgt_kiosk.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable wbgt-kiosk.service
sudo systemctl start wbgt-kiosk.service
```

### crontab使用
```bash
crontab -e
# 以下を追加
@reboot cd /home/pi/wbgt && python3 wbgt_kiosk.py
```

## 📊 表示内容

### 天気情報
- 現在気温
- 湿度
- 天気概況
- 体感温度

### WBGT指数
- **WBGT値** - 熱中症リスクの指標
- **警戒レベル** - 注意/警戒/厳重警戒/危険/極めて危険
- **アドバイス** - 具体的な対応策

### 熱中症警戒アラート
- 今日の警戒レベル
- 明日の警戒レベル

## 📁 ファイル構成

```
wbgt/
├── wbgt_kiosk.py        # メインアプリケーション
├── jma_api.py           # 気象庁API クライアント
├── heatstroke_alert.py  # 熱中症警戒アラート
├── config.py            # 設定ファイル
├── config.sample.py     # 設定サンプル
├── requirements.txt     # Python依存関係
├── install.sh           # セットアップスクリプト
├── autostart.sh         # 自動起動スクリプト
└── README.md           # このファイル
```

## 🌐 API

- **気象庁API** - 天気情報・熱中症警戒アラート
- **APIキー不要** - 無料で利用可能
- **信頼性の高いデータ** - 日本の公式気象データ

## 🔍 トラブルシューティング

### よくある問題

**Q: ウィンドウが表示されない（GUI版）**
A: ターミナル版をお試しください：`python3 wbgt_kiosk.py`

**Q: データが取得できない**
A: インターネット接続を確認してください

**Q: 地域を変更したい**
A: `config.py`の`AREA_CODE`を変更してください

### ログ確認
```bash
tail -f wbgt_kiosk.log
```

## 🤝 貢献

バグ報告や機能要望は Issues にてお願いします。

## 📄 ライセンス

MIT License

## 🏷️ バージョン

Version 1.0.0 - 2025年6月