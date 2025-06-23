# WBGT熱中症警戒キオスク - Windows版セットアップガイド

## 📋 必要な環境

- Windows 10/11
- Python 3.8以上
- インターネット接続

## 🚀 インストール方法

### 方法1: 通常インストール（推奨）

1. **リポジトリをダウンロード**
   ```
   git clone [repository-url]
   cd wbgt
   ```

2. **セットアップスクリプトを実行**
   ```
   install.bat
   ```

3. **動作確認**
   ```
   python wbgt_kiosk.py --demo
   ```

### 方法2: 仮想環境を使用したインストール

1. **仮想環境セットアップ**
   ```
   setup_venv.bat
   ```

2. **仮想環境での実行**
   ```
   run_wbgt.bat --demo
   ```

## 🎮 使用方法

### コマンドライン実行

- **デモモード**: `python wbgt_kiosk.py --demo`
- **通常モード**: `python wbgt_kiosk.py`
- **GUI版**: `python wbgt_kiosk.py --gui`

### 仮想環境での実行

- **デモモード**: `run_wbgt.bat --demo`
- **通常モード**: `run_wbgt.bat`
- **GUI版**: `run_wbgt.bat --gui`

## ⚙️ 設定

1. **設定ファイルの編集**
   ```
   notepad config.py
   ```

2. **主な設定項目**
   - `LOCATIONS`: 監視地域の設定
   - `UPDATE_INTERVAL_MINUTES`: 更新間隔（分）
   - `DISPLAY_*`: GUI版の表示設定

## 🔧 自動起動設定

### Windowsサービスとして実行（推奨）

1. **PowerShellを管理者として実行**

2. **サービスインストール**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   .\install_windows_service.ps1
   ```

3. **サービス管理**
   - 開始: `Start-Service -Name WBGTKiosk`
   - 停止: `Stop-Service -Name WBGTKiosk`
   - 状態確認: `Get-Service -Name WBGTKiosk`

4. **サービス削除**
   ```powershell
   .\uninstall_windows_service.ps1
   ```

### タスクスケジューラを使用

1. **タスクスケジューラを開く**
   - `Win + R` → `taskschd.msc`

2. **基本タスクの作成**
   - トリガー: コンピューターの起動時
   - 操作: プログラムの開始
   - プログラム: `[インストールパス]\autostart.bat`

## 📊 ログ確認

### ターミナル版ログ
- コンソール出力で確認

### サービス版ログ
```powershell
# 最新20行を表示
Get-Content .\service.log -Tail 20

# リアルタイム監視
Get-Content .\service.log -Wait
```

### 自動起動ログ
```
type autostart.log
```

## 🛠️ トラブルシューティング

### Python関連エラー

**エラー**: `'python' は、内部コマンドまたは外部コマンド...`
**解決**: Python公式サイトからインストール
- https://www.python.org/downloads/
- インストール時に「Add Python to PATH」をチェック

### 依存関係エラー

**エラー**: `ModuleNotFoundError`
**解決**:
```
pip install -r requirements.txt
```

### GUI版エラー

**エラー**: `tkinterが利用できません`
**解決**: Python再インストール時に「tcl/tk and IDLE」を有効化

### サービス関連エラー

**エラー**: サービス開始失敗
**解決**:
1. ログファイル確認: `Get-Content .\service.log`
2. 手動実行テスト: `python wbgt_kiosk.py --demo`
3. パス設定確認

### ネットワークエラー

**エラー**: API接続失敗
**解決**:
1. インターネット接続確認
2. ファイアウォール設定確認
3. プロキシ設定（企業環境の場合）

## 📁 ファイル構成

### Windows専用ファイル
- `install.bat` - メインインストールスクリプト
- `setup_venv.bat` - 仮想環境セットアップ
- `run_wbgt.bat` - 仮想環境実行スクリプト
- `autostart.bat` - 自動起動スクリプト
- `install_windows_service.ps1` - サービスインストール
- `uninstall_windows_service.ps1` - サービス削除
- `WINDOWS_README.md` - このファイル

### 共通ファイル
- `wbgt_kiosk.py` - メインアプリケーション
- `config.py` - 設定ファイル（コピーで作成）
- `config.sample.py` - 設定テンプレート
- `requirements.txt` - Python依存関係

## 🔄 アップデート

1. **ファイルのバックアップ**
   ```
   copy config.py config_backup.py
   ```

2. **新しいバージョンをダウンロード**

3. **設定ファイルを復元**
   ```
   copy config_backup.py config.py
   ```

4. **依存関係を更新**
   ```
   pip install -r requirements.txt --upgrade
   ```

## 📞 サポート

### ログファイルの場所
- アプリケーションログ: `wbgt_kiosk.log`
- 自動起動ログ: `autostart.log`
- サービスログ: `service.log`

### 設定リセット
```
copy config.sample.py config.py
```

### 完全リセット
1. サービス停止・削除
2. 仮想環境削除: `rmdir /s venv`
3. 再インストール実行