# 🚀 WBGT熱中症警戒キオスク クイックスタートガイド

## 📋 簡単3ステップ

### 1️⃣ セットアップ
```bash
./setup_venv.sh
```
> **初回のみ実行**：仮想環境の作成と依存関係のインストール

### 2️⃣ 動作確認
```bash
./run_wbgt.sh --demo
```
> **デモモード**：3回データ更新して終了

### 3️⃣ 本格運用
```bash
./run_wbgt.sh
```
> **通常モード**：30分ごとの自動更新

## ❗ よくあるエラーと解決方法

### `ModuleNotFoundError: No module named 'requests'`
```bash
# 仮想環境をセットアップして実行
./setup_venv.sh
./run_wbgt.sh --demo
```

### `Permission denied`
```bash
# 実行権限を付与
chmod +x setup_venv.sh run_wbgt.sh
./setup_venv.sh
```

### `python3: command not found`
```bash
# Python3をインストール
# macOS: 
brew install python3
# Raspberry Pi OS:
sudo apt update && sudo apt install python3
```

## 🗾 地域変更

### 東京以外の地域に変更する場合
```bash
nano config.py
```

### 設定例
```python
# 大阪の場合
AREA_CODE = "270000"
CITY_NAME = "大阪"

# 福岡の場合  
AREA_CODE = "400000"
CITY_NAME = "福岡"
```

## 🔧 オプション

```bash
./run_wbgt.sh --demo    # デモモード（短時間テスト）
./run_wbgt.sh           # 通常モード（継続動作）
./run_wbgt.sh --gui     # GUI版（実験的）
./run_wbgt.sh --help    # ヘルプ表示
```

## 🆘 困った時は

1. **ログを確認**：`tail -f wbgt_kiosk.log`
2. **再セットアップ**：`rm -rf venv && ./setup_venv.sh`
3. **詳細ドキュメント**：`README.md`を参照

---
**🎯 目標**：`./run_wbgt.sh --demo` が正常に動作すれば成功です！