# SSL証明書認証の設定 (Windows企業環境対応)

## 概要

このWBGT熱中症監視システムでは、Windows企業環境でのSSL証明書認証の問題に対応するための設定オプションを追加しました。

## 問題の背景

企業環境のWindowsでは以下のような問題が発生することがあります：
- 企業のファイアウォールやプロキシによるSSL証明書の問題
- 社内の証明書認証局による証明書検証の問題
- ネットワークセキュリティポリシーによる接続制限

## 解決策

### 1. 設定ファイルの編集

`setup/config.py` ファイルで以下の設定を変更できます：

```python
# SSL設定（Windows企業環境向け）
SSL_VERIFY = False  # SSL証明書検証をスキップする場合はFalse
SSL_CERT_PATH = None  # カスタム証明書パスがある場合に設定
```

### 2. 設定オプション

- **SSL_VERIFY**: 
  - `True` (デフォルト): SSL証明書の検証を行います（推奨）
  - `False`: SSL証明書の検証をスキップします（企業環境向け）

- **SSL_CERT_PATH**: 
  - `None` (デフォルト): システムの標準証明書を使用
  - カスタム証明書ファイルのパスを指定可能

### 3. 対象API

以下のAPIクライアントがSSL設定に対応しています：
- 環境省WBGT API (`env_wbgt_api.py`, `env_wbgt_api_en.py`)
- 気象庁API (`jma_api.py`, `jma_api_en.py`)
- 熱中症警戒アラート (`heatstroke_alert.py`, `heatstroke_alert_en.py`)

## 使用方法

### 企業環境でSSL証明書エラーが発生する場合

1. `setup/config.py` を開く
2. `SSL_VERIFY = False` に変更
3. アプリケーションを再起動

### 警告メッセージ

SSL検証を無効にした場合、ログに以下の警告が表示されます：
- 日本語版: "SSL証明書検証が無効化されています（企業環境向け設定）"
- 英語版: "SSL certificate verification disabled (corporate environment setting)"

## セキュリティ注意事項

- SSL証明書検証を無効にすると、中間者攻撃のリスクが増加します
- 本設定は企業環境での一時的な対処法として使用してください
- 可能な限り、適切な証明書設定を行い `SSL_VERIFY = True` で使用することを推奨します

## トラブルシューティング

### よくあるSSLエラー

1. **証明書検証エラー**
   ```
   SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
   ```
   → `SSL_VERIFY = False` に設定

2. **プロキシ関連エラー**
   ```
   ProxyError: Cannot connect to proxy
   ```
   → ネットワーク管理者に相談し、プロキシ設定を確認

3. **urllib3警告の抑制**
   SSL検証を無効にした場合、urllib3の警告メッセージは自動的に抑制されます。

## 実装詳細

各APIクライアントの`__init__`メソッドで以下の処理を行います：

1. 設定ファイルからSSL設定を読み込み
2. SSL検証が無効の場合、urllib3警告を抑制
3. 全ての HTTP リクエストに `verify` パラメータを適用

これにより、アプリケーション全体で一貫したSSL証明書の取り扱いが可能になります。