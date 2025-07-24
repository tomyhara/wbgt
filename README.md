# WBGT熱中症警戒キオスク端末

熱中症警戒アラート情報と天気予報を表示するキオスク端末システムです。環境省公式WBGT指数と気象庁データを使用し、複数地点の監視に対応しています。

## ✨ 主要機能

- 🌡️ **WBGT指数表示** - 環境省公式データ優先、気象庁APIフォールバック
- 🚨 **熱中症警戒アラート** - 今日・明日の警戒レベル表示
- 🌤️ **リアルタイム天気情報** - 気象庁APIから取得
- 🏢 **複数地点対応** - 最大複数都市の同時監視
- 🎯 **データソース表示** - 環境省公式/計算値の区別を明示
- 🎨 **色分け表示** - 危険度に応じた視覚的な警告
- 🔄 **自動更新** - 設定可能な間隔でのデータ更新
- 📅 **季節対応** - 環境省サービス期間（4-10月）の自動判定
- 📁 **CSVモード** - SSL証明書問題に対応したオフライン動作
- 🌐 **多言語対応** - 日本語・英語版を提供

## 🛠️ 必要な環境

- Python 3.8以上
- インターネット接続
- 対応OS: Linux, macOS, Windows
- 推奨環境: Raspberry Pi 3以上、ディスプレイ

## 🚀 クイックスタート

### 1. リポジトリの取得
```bash
git clone <repository-url>
cd wbgt
```

### 2. 依存関係のインストール
```bash
# 仮想環境セットアップ（推奨）
./setup/setup_venv.sh

# または直接インストール
pip install -r setup/requirements.txt
```

### 3. 設定ファイルの作成
```bash
# JSONコンフィグ（推奨）
cp setup/config.json setup/config.json.bak
nano setup/config.json

# OpenWeatherMap APIキーを設定（オプション）
# "YOUR_OPENWEATHERMAP_API_KEY_HERE" を実際のAPIキーに置換

# または従来のPythonコンフィグ
cp setup/config.sample.py setup/config.py
nano setup/config.py
```

### 4. 動作確認
```bash
# デモモード（動作確認用）
python3 src/wbgt_kiosk.py --demo

# 通常モード
python3 src/wbgt_kiosk.py
```

## 📱 使用方法

### 基本コマンド
```bash
# 日本語版（ターミナル）
python3 src/wbgt_kiosk.py

# 英語版（ターミナル）
python3 src/wbgt_kiosk_en.py

# デモモード（3回更新で終了）
python3 src/wbgt_kiosk.py --demo

# GUI版（実験的）
python3 src/wbgt_kiosk.py --gui
```

### 実行スクリプト使用
```bash
# 統合スクリプト
./scripts/wbgt.sh --demo

# 個別スクリプト
./scripts/run_wbgt.sh --demo      # 日本語版
./scripts/run_wbgt_en.sh --demo   # 英語版
```

### 操作方法
- **Ctrl+C**: アプリケーション終了
- **自動更新**: 設定可能（デフォルト30分間隔、デモモードは5秒間隔）

## ⚙️ 設定

### JSONコンフィグ（推奨）

`setup/config.json`で複数地点を設定：

```json
{
  "locations": [
    {
      "name": "横浜",
      "area_code": "140000",
      "wbgt_location_code": "46106",
      "prefecture": "神奈川県"
    },
    {
      "name": "東京",
      "area_code": "130000",
      "wbgt_location_code": "44132",
      "prefecture": "東京都"
    }
  ],
  "update_interval_minutes": 30,
  "display": {
    "width": 800,
    "height": 600,
    "fullscreen": false
  },
  "openweather_api_key": "YOUR_OPENWEATHERMAP_API_KEY_HERE",
  "weather_api": {
    "provider": "openweathermap",
    "fallback_to_jma": true,
    "timeout": 10
  }
}
```

#### OpenWeatherMap APIキーの設定

1. **APIキー取得**:
   - [OpenWeatherMap](https://openweathermap.org/api) でアカウント作成
   - 無料プランで1,000 calls/day利用可能
   - API Keysページでキーを取得

2. **設定ファイル更新**:
   ```bash
   # config.jsonを編集
   nano setup/config.json
   
   # "YOUR_OPENWEATHERMAP_API_KEY_HERE" を実際のAPIキーに置換
   "openweather_api_key": "abcd1234your_actual_api_key_here"
   ```

3. **簡単設定スクリプト**:
   ```bash
   # 対話式でAPIキーを設定
   ./scripts/setup_openweather_api.sh
   ```

4. **動作確認**:
   ```bash
   # OpenWeatherMapデータのテスト
   python3 test_openweather_offline.py
   ```

**注意**: APIキーが設定されていない場合、システムは自動的にオフラインモードや気象庁APIにフォールバックします。

### Pythonコンフィグ（従来方式）

`setup/config.py`で設定：

```python
LOCATIONS = [
    {
        "name": "横浜",
        "area_code": "140000",
        "wbgt_location_code": "46106",
        "prefecture": "神奈川県"
    }
]
```

### 主要都市コード

| 都市 | area_code | wbgt_location_code |
|------|-----------|-------------------|
| 東京 | 130000 | 44132 |
| 横浜 | 140000 | 46106 |
| 大阪 | 270000 | 47772 |
| 名古屋 | 230000 | 47636 |
| 福岡 | 400000 | 82142 |

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
ExecStart=/usr/bin/python3 /home/pi/wbgt/src/wbgt_kiosk.py
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
@reboot cd /home/pi/wbgt && python3 src/wbgt_kiosk.py
```

## 📊 表示内容

### 天気情報
- 現在気温
- 湿度
- 天気概況
- 体感温度

### WBGT指数
- **WBGT値** - 熱中症リスクの指標
- **データソース** - 環境省公式データ優先、気象庁計算値フォールバック
- **警戒レベル** - ほぼ安全/注意/警戒/厳重警戒/危険
- **アドバイス** - 具体的な対応策
- **季節対応** - 環境省サービス期間（4-10月）自動判定

### 熱中症警戒アラート
- 今日の警戒レベル
- 明日の警戒レベル

## 📁 プロジェクト構成

```
wbgt/
├── src/                          # 🎯 メインソースコード
│   ├── wbgt_kiosk.py            # メインアプリケーション（日本語版）
│   ├── wbgt_kiosk_en.py         # メインアプリケーション（英語版）
│   ├── jma_api.py               # 気象庁API クライアント
│   ├── jma_api_en.py            # 気象庁API クライアント（英語版）
│   ├── env_wbgt_api.py          # 環境省WBGT API クライアント
│   ├── env_wbgt_api_en.py       # 環境省WBGT API クライアント（英語版）
│   ├── heatstroke_alert.py      # 熱中症警戒アラート
│   └── heatstroke_alert_en.py   # 熱中症警戒アラート（英語版）
├── setup/                        # ⚙️ 設定・セットアップ
│   ├── config.json              # 設定ファイル（JSON形式・推奨）
│   ├── config_loader.py         # 設定ローダー（JSON/Python対応）
│   ├── config.py                # 設定ファイル（Python形式）
│   ├── config.sample.py         # 設定サンプル（日本語版）
│   ├── config_en.py             # 設定ファイル（英語版）
│   ├── config_en.sample.py      # 設定サンプル（英語版）
│   ├── requirements.txt         # Python依存関係
│   ├── setup_venv.sh            # 仮想環境セットアップ（Unix）
│   ├── setup_venv.bat           # 仮想環境セットアップ（Windows）
│   ├── install.sh               # セットアップスクリプト（Unix）
│   └── install.bat              # セットアップスクリプト（Windows）
├── scripts/                      # 🚀 実行・ダウンロードスクリプト
│   ├── wbgt.sh                  # 統合ランチャー（Unix）
│   ├── wbgt.bat                 # 統合ランチャー（Windows）
│   ├── run_wbgt.sh              # 実行スクリプト（日本語版）
│   ├── run_wbgt_en.sh           # 実行スクリプト（英語版）
│   ├── run_with_csv.sh          # CSVモード実行スクリプト
│   ├── download_all_data.sh     # 全データダウンロード
│   ├── download_jma_data.sh     # JMA気象データダウンロード
│   ├── download_wbgt_data.sh    # 環境省WBGTデータダウンロード
│   ├── get_config.py            # 設定読み取りスクリプト
│   ├── autostart.sh             # 自動起動スクリプト（Unix）
│   └── autostart.bat            # 自動起動スクリプト（Windows）
├── data/csv/                     # 📁 CSVモード用データ
├── logs/                         # 📁 ログファイル
├── venv/                         # 📁 Python仮想環境
├── test_csv_mode.py             # 🧪 CSVモードテストスクリプト
├── wbgt-kiosk.service           # ⚙️ systemdサービス設定
├── README.md                    # 📖 ドキュメント（日本語版）
├── README_EN.md                 # 📖 ドキュメント（英語版）
├── CSV_USAGE_README.md          # 📖 CSVモード使用方法
├── QUICKSTART.md                # 📖 クイックスタートガイド
├── SSL_README.md                # 📖 SSL問題対応ガイド
└── doc/                         # 📚 参考ドキュメント
```

## 🌐 API

- **環境省熱中症予防情報サイト** - 公式WBGT指数（4-10月期間）
- **気象庁API** - 天気情報・熱中症警戒アラート・WBGT計算値
- **APIキー不要** - 無料で利用可能
- **ハイブリッド方式** - 公式データ優先、フォールバック対応
- **信頼性の高いデータ** - 日本の公式気象データ

## 📁 CSVモード（オフライン動作）

### SSL証明書問題とCSVモード

企業環境やネットワーク制限でSSL証明書の問題が発生する場合、CSVモードでオフライン動作が可能です。

#### CSVモードの使用方法

**1. データダウンロード（初回・定期実行）：**
```bash
./scripts/download_all_data.sh
# または
./scripts/run_with_csv.sh --download-only
```

**2. CSVデータでシステム実行：**
```bash
# 日本語版
./scripts/run_with_csv.sh

# 英語版
./scripts/run_with_csv.sh --english

# 既存データのみ使用（ダウンロードなし）
./scripts/run_with_csv.sh --run-only
```

#### 個別データダウンロード
```bash
# JMA気象データのみ
./scripts/download_jma_data.sh

# 環境省WBGTデータのみ  
./scripts/download_wbgt_data.sh

# 設定確認
python3 scripts/get_config.py locations
```

#### CSVモードのテスト
```bash
python3 test_csv_mode.py
```

**注意**: CSVモードは設定ファイル（`setup/config.json`または`setup/config.py`）の地域設定に基づいてデータをダウンロードします。

詳細は [CSV_USAGE_README.md](CSV_USAGE_README.md) をご覧ください。

## 🔍 トラブルシューティング

### よくある問題

**Q: `ModuleNotFoundError: No module named 'requests'` エラー**
```bash
# 依存関係をインストール
pip install -r setup/requirements.txt

# または仮想環境使用
./setup/setup_venv.sh
source venv/bin/activate
```

**Q: 設定ファイルが見つからない**
```bash
# JSONコンフィグを作成
cp setup/config.json setup/config.json.bak
nano setup/config.json

# または従来のPythonコンフィグ
cp setup/config.sample.py setup/config.py
```

**Q: SSL証明書エラーが発生する**
```bash
# CSVモードでオフライン動作
./scripts/download_all_data.sh      # データダウンロード
./scripts/run_with_csv.sh --run-only # CSVデータで実行
```

**Q: データが取得できない**
- インターネット接続を確認
- ファイアウォール設定を確認
- CSVモードを試用：`./scripts/run_with_csv.sh`

**Q: 地域を変更したい**
```bash
# JSONコンフィグの場合
nano setup/config.json

# Pythonコンフィグの場合  
nano setup/config.py
```

**Q: GUI版でウィンドウが表示されない**
```bash
# ターミナル版を使用
python3 src/wbgt_kiosk.py

# tkinterをインストール（Linux）
sudo apt-get install python3-tk
```

**Q: スクリプトの実行権限エラー**
```bash
chmod +x scripts/*.sh
./scripts/run_wbgt.sh --demo
```

### ログ確認
```bash
# アプリケーションログ
tail -f wbgt_kiosk.log
tail -f scripts/wbgt_kiosk.log

# CSVダウンロードログ
tail -f logs/master_download.log
tail -f logs/jma_download.log
tail -f logs/wbgt_download.log
```

### 設定確認コマンド
```bash
# 現在の設定を確認
python3 scripts/get_config.py locations
python3 scripts/get_config.py area_codes
python3 scripts/get_config.py prefectures

# CSVモードのテスト
python3 test_csv_mode.py
```

## 🔗 関連ドキュメント

- [QUICKSTART.md](QUICKSTART.md) - クイックスタートガイド
- [CSV_USAGE_README.md](CSV_USAGE_README.md) - CSVモード詳細ガイド
- [SSL_README.md](SSL_README.md) - SSL証明書問題対応
- [LANGUAGE_SWITCHING.md](LANGUAGE_SWITCHING.md) - 多言語対応について
- [WINDOWS_README.md](WINDOWS_README.md) - Windows環境向けガイド

## 🤝 貢献・サポート

- バグ報告や機能要望は Issues にてお願いします
- プルリクエストも歓迎します
- セキュリティ問題は個別にご連絡ください

## 📄 ライセンス

MIT License - 熱中症予防と公共安全のためのオープンソースプロジェクト

## 🏷️ バージョン

**Version 2.0.0** - 2025年7月
- JSON設定ファイル対応
- CSVダウンロードスクリプトの設定連携
- 複数地点監視対応
- 後方互換性維持

---

**⚠️ 重要**: このシステムは情報提供を目的としています。熱中症の症状を感じた場合は医療機関にご相談ください。公式の警戒アラートに従ってください。