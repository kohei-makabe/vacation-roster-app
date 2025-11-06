import streamlit as st
from email.message import EmailMessage
import smtplib, ssl
from datetime import date
import pandas as pd
from pathlib import Path

# ----------------------------
# ページ設定
# ----------------------------
st.set_page_config(page_title="休暇申請＆勤務表", page_icon="🗓️", layout="centered")
st.title("🗓️ 休暇申請 & 勤務表ビュー（スマホ対応）")

# ----------------------------
# 共通：保存フォルダ
# ----------------------------
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
LOG_PATH = DATA_DIR / "vacation_log.csv"
ROSTER_PATH = DATA_DIR / "roster_latest.parquet"  # 勤務表の保存先（堅牢＆高速）

# ----------------------------
# 休暇申請（前作のまま）
# ----------------------------
TYPE_OPTIONS = ["有給", "半休", "夏休み"]

def load_log() -> pd.DataFrame:
    if LOG_PATH.exists():
        return pd.read_csv(LOG_PATH)
    return pd.DataFrame(columns=[
        "timestamp", "applicant", "type", "date", "status", "to", "cc", "message_id"
    ])

def save_log(df: pd.DataFrame) -> None:
    df.to_csv(LOG_PATH, index=False)

def send_mail(vtype: str, d: date, applicant: str) -> EmailMessage:
    body = (
        f"{applicant}です。\n"
        f"{d.strftime('%Y-%m-%d')} に {vtype} を取得いたします。\n"
        "本メールは申請フォームからの自動送信です。ご確認よろしくお願いいたします。"
    )
    msg = EmailMessage()
    msg["Subject"] = f"休暇申請（{applicant}）"
    msg["From"] = st.secrets["MAIL_FROM"]
    msg["To"] = st.secrets["MAIL_TO"]
    cc = st.secrets.get("MAIL_CC", "")
    if cc:
        msg["Cc"] = cc
    bcc = st.secrets.get("MAIL_BCC", "")
    msg.set_content(body)

    host = st.secrets["SMTP_HOST"]
    port = int(st.secrets.get("SMTP_PORT", 587))
    user = st.secrets["SMTP_USER"]
    password = st.secrets["SMTP_PASS"]

    with smtplib.SMTP(host, port) as server:
        server.starttls(context=ssl.create_default_context())
        server.login(user, password)
        to_addrs = [st.secrets["MAIL_TO"]]
        if cc:
            to_addrs += [a.strip() for a in cc.split(",") if a.strip()]
        if bcc:
            to_addrs += [a.strip() for a in bcc.split(",") if a.strip()]
        server.send_message(msg, to_addrs=to_addrs)
    return msg

# ----------------------------
# 勤務表：保存/読込
# ----------------------------
def save_roster(df: pd.DataFrame) -> None:
    df.columns = [str(c).strip() for c in df.columns]
    df.to_parquet(ROSTER_PATH, index=False)

def load_roster() -> pd.DataFrame | None:
    if ROSTER_PATH.exists():
        return pd.read_parquet(ROSTER_PATH)
    return None

# ----------------------------
# パスコードチェック（閲覧保護）
# ----------------------------
def check_passcode() -> bool:
    required = st.secrets.get("ROSTER_PASSCODE", "")
    if not required:
        st.warning("管理者設定：ROSTER_PASSCODE が未設定です（誰でも閲覧可）。")
        return True
    qp = st.query_params
    code_qp = qp.get("code", [""])[0] if hasattr(qp, "get") else ""
    if code_qp == required:
        return True
    entered = st.text_input("閲覧パスコード", type="password", placeholder="例）123456")
    ok = st.button("認証する", use_container_width=True)
    if ok and entered == required:
        st.success("認証に成功しました。")
        try:
            st.query_params["code"] = entered
        except Exception:
            pass
        return True
    if ok and entered != required:
        st.error("パスコードが違います。")
    return False

# ----------------------------
# UI：タブ
# ----------------------------
tab1, tab2 = st.tabs(["📨 休暇申請", "📋 勤務表"])

with tab1:
    st.caption("・種類と日付を選んで「申請する」だけ。文面は固定で上長に自動送信します。")
    applicant = st.text_input("申請者名", value=st.secrets.get("APPLICANT_NAME", ""), placeholder="例）眞壁 耕平")
    vtype = st.selectbox("休暇種類", TYPE_OPTIONS, index=0)
    d = st.date_input("日付を選択", value=date.today())
    st.caption("※まずは簡易運用。必要なら午前/午後の区分も後で追加できます。")
    send_disabled = (not applicant)
    if st.button("申請する", type="primary", use_container_width=True, disabled=send_disabled):
        try:
            msg = send_mail(vtype, d, applicant)
            st.success("申請メールを送信しました。")
            df = load_log()
            new = pd.DataFrame([{
                "timestamp": pd.Timestamp.now(tz="Asia/Tokyo"),
                "applicant": applicant,
                "type": vtype,
                "date": d.isoformat(),
                "status": "sent",
                "to": st.secrets["MAIL_TO"],
                "cc": st.secrets.get("MAIL_CC", ""),
                "message_id": msg.get("Message-Id", "")
            }])
            df = pd.concat([new, df], ignore_index=True)
            save_log(df)
        except Exception as e:
            st.error(f"送信に失敗しました：{e}")

    st.subheader("履歴")
    df_hist = load_log()
    if df_hist.empty:
        st.info("まだ履歴はありません。")
    else:
        st.dataframe(df_hist.head(100), use_container_width=True)
        st.download_button(
            "CSVをダウンロード",
            data=df_hist.to_csv(index=False).encode("utf-8-sig"),
            file_name="vacation_log.csv",
            mime="text/csv",
            use_container_width=True
        )

with tab2:
    st.caption("・最新の勤務表をアップロードし、認証済みの人だけが閲覧できます。")
    authed = check_passcode()
    if authed:
        st.success("勤務表の閲覧・更新が可能です。")
        roster_df = load_roster()
        if roster_df is not None and not roster_df.empty:
            st.subheader("現在の勤務表（最新）")
            st.dataframe(roster_df, use_container_width=True, height=480)
            st.download_button(
                "勤務表CSVをダウンロード",
                data=roster_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="roster_latest.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("まだ勤務表が登録されていません。")

        st.divider()
        st.subheader("勤務表のアップロード（CSV / XLSX）")
        up = st.file_uploader("ファイルを選択", type=["csv", "xlsx"])
        if up:
            try:
                if up.name.lower().endswith(".csv"):
                    new_df = pd.read_csv(up)
                else:
                    new_df = pd.read_excel(up)
                if new_df.empty:
                    st.error("ファイルにデータがありません。")
                else:
                    save_roster(new_df)
                    st.success("勤務表を更新しました。ページを再読み込みすると反映されます。")
            except Exception as e:
                st.error(f"読込に失敗しました：{e}")

st.caption("© Simple Vacation Mailer + Roster Viewer")
