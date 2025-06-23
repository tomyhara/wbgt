# WBGT Kiosk Language Switching Guide

このガイドでは、WBGTキオスクの言語切り替え機能について説明します。

## 🌍 サポート言語 / Supported Languages

- **日本語 (Japanese)**: `ja`, `jp`, `japanese`
- **English**: `en`, `english`
- **自動検出 (Auto-detect)**: `auto`

## 🚀 基本的な使用方法 / Basic Usage

### Linux/macOS

```bash
# 統合ランチャーを使用
./wbgt.sh ja --demo          # 日本語版デモ
./wbgt.sh en --gui           # 英語版GUI
./wbgt.sh auto               # 自動言語検出

# シンプルランチャー（推奨）
./wbgt ja --demo             # 日本語版デモ
./wbgt en --gui              # 英語版GUI
./wbgt auto                  # 自動言語検出
```

### Windows

```cmd
REM 統合ランチャーを使用
wbgt.bat ja --demo           REM 日本語版デモ
wbgt.bat en --gui            REM 英語版GUI
wbgt.bat auto                REM 自動言語検出
```

## 📋 詳細コマンド例 / Detailed Command Examples

### 1. 言語指定実行

```bash
# 日本語版
./wbgt ja                    # 通常モード
./wbgt japanese --demo       # デモモード
./wbgt jp --gui              # GUI版

# 英語版
./wbgt en                    # Normal mode
./wbgt english --demo        # Demo mode
./wbgt en --gui              # GUI version
```

### 2. 自動言語検出

```bash
# システム言語を自動検出して実行
./wbgt auto
./wbgt auto --demo
./wbgt auto --gui
```

### 3. ヘルプ表示

```bash
./wbgt --help
./wbgt -h
```

## ⚙️ 言語検出ロジック / Language Detection Logic

### Linux/macOS
システムの `LANG` 環境変数を確認:
- `ja*` → 日本語版
- `en*` → 英語版
- その他 → 英語版（デフォルト）

### Windows
以下の順序で言語を検出:
1. `LANG` 環境変数
2. Windows ロケール設定
3. デフォルト: 英語版

## 🔧 仮想環境との連携 / Virtual Environment Integration

ランチャーは自動的に仮想環境を検出して使用します：

```bash
# 仮想環境がある場合
./wbgt ja --demo             # 自動的にvenv/bin/activateを実行

# 仮想環境がない場合
./wbgt ja --demo             # システムのPythonを使用
```

## 📁 ファイル構成 / File Structure

```
wbgt/
├── wbgt                     # シンプルランチャー (Linux/macOS)
├── wbgt.sh                  # 統合ランチャー (Linux/macOS)
├── wbgt.bat                 # 統合ランチャー (Windows)
├── wbgt_kiosk.py           # 日本語版メインアプリ
├── wbgt_kiosk_en.py        # 英語版メインアプリ
├── config.py               # 日本語版設定
├── config_en.py            # 英語版設定
└── venv/                   # 仮想環境（オプション）
```

## 🎯 使用例とユースケース / Use Cases and Examples

### 1. 開発・テスト環境

```bash
# デモモードで各言語をテスト
./wbgt ja --demo
./wbgt en --demo

# GUI版で見た目確認
./wbgt ja --gui
./wbgt en --gui
```

### 2. 本番環境

```bash
# システム言語に応じて自動起動
./wbgt auto

# 明示的に言語指定
./wbgt ja                    # 日本語環境
./wbgt en                    # 英語環境
```

### 3. 国際化対応

```bash
# 環境変数でシステム言語を設定
export LANG=ja_JP.UTF-8
./wbgt auto                  # 日本語版で起動

export LANG=en_US.UTF-8
./wbgt auto                  # 英語版で起動
```

## 🛠️ トラブルシューティング / Troubleshooting

### よくある問題 / Common Issues

**1. 言語が正しく検出されない**
```bash
# 明示的に指定
./wbgt ja --demo             # 強制的に日本語
./wbgt en --demo             # 強制的に英語
```

**2. 実行権限エラー (Linux/macOS)**
```bash
chmod +x wbgt wbgt.sh
```

**3. 仮想環境が見つからない**
```bash
# 仮想環境セットアップ
./setup_venv.sh              # Linux/macOS
setup_venv.bat               # Windows
```

**4. 設定ファイルエラー**
```bash
# 設定ファイル作成
cp config.sample.py config.py              # 日本語版
cp config_en.sample.py config_en.py        # 英語版
```

### デバッグモード / Debug Mode

詳細な動作確認には直接Pythonスクリプトを実行:

```bash
# 日本語版
python wbgt_kiosk.py --demo

# 英語版
python wbgt_kiosk_en.py --demo
```

## 🔄 自動起動設定 / Autostart Configuration

### systemd (Linux)

```bash
# サービスファイル編集
sudo nano /etc/systemd/system/wbgt-kiosk.service

[Unit]
Description=WBGT Kiosk Auto Language
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wbgt
ExecStart=/home/pi/wbgt/wbgt auto
Restart=always

[Install]
WantedBy=multi-user.target
```

### Windows Task Scheduler

1. タスクスケジューラを開く
2. 基本タスクを作成
3. プログラム: `C:\path\to\wbgt\wbgt.bat`
4. 引数: `auto`

## 📊 パフォーマンス / Performance

ランチャーのオーバーヘッドは最小限:
- 言語検出: < 100ms
- 仮想環境アクティベート: < 200ms
- アプリ起動: 通常通り

## 🔒 セキュリティ / Security

- 入力検証済み
- パス traversal攻撃対策済み
- 環境変数の安全な処理

---

このガイドにより、多言語環境でのWBGTキオスクの運用が簡単になります。