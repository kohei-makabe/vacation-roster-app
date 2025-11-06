# 休暇申請 & 勤務表ビュー（Streamlit）

スマホから **休暇種類＋日付＋申請ボタン** だけで上長に自動メール。  
勤務表（CSV/XLSX）をアップロードして、**パスコード**を知る人だけが閲覧できる簡易ビューも同居。

## ローカル実行

```bash
pip install -r requirements.txt
streamlit run app.py
```

`.streamlit/secrets.toml` を作成して下記を設定：

```toml
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USER = "you@example.com"
SMTP_PASS = "app_password"

MAIL_FROM = "you@example.com"
MAIL_TO   = "boss@example.com"
MAIL_CC   = ""
MAIL_BCC  = ""

APPLICANT_NAME = "眞壁 耕平"

ROSTER_PASSCODE = "123456"
```

## デプロイ（Streamlit Community Cloud）

- GitHub にこのリポジトリをプッシュ
- Streamlit Cloud で「New app」→ リポジトリを選択 → `app.py`
- 「Settings → Secrets」に上記の `secrets.toml` の内容を貼り付けて保存

## 注意

- Cloud のローカルファイルは再デプロイ等で消える場合があります。重要な勤務表や履歴 CSV は随時ダウンロードしてください。
- 本格的な認証が必要なら `streamlit-authenticator` や外部IDプロバイダ（Google/Okta 等）＋Cloud Run などをご検討ください。
