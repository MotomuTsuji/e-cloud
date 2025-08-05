import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2 import credentials
import os
import json
from googleapiclient.discovery import build

# OAuth2設定
CLIENT_SECRETS_FILE = "client_secrets.json" # 一時ファイルとして作成
SCOPES = ["https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile", "openid"]

def create_client_secrets_file():
    """Streamlit secretsからクライアントIDとシークレットを読み込み、一時ファイルを作成する"""
    client_id = st.secrets["GOOGLE_CLIENT_ID"]
    client_secret = st.secrets["GOOGLE_CLIENT_SECRET"]

    client_secrets_data = {
        "web": {
            "client_id": client_id,
            "project_id": "erika-ai-chat", # プロジェクトIDは適宜変更
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": ["http://localhost:8501", "https://your-app-name.streamlit.app"], # デプロイ後のURLも追加
            "javascript_origins": ["http://localhost:8501", "https://your-app-name.streamlit.app"] # デプロイ後のURLも追加
        }
    }
    with open(CLIENT_SECRETS_FILE, "w") as f:
        json.dump(client_secrets_data, f)

def get_flow():
    """OAuth2フローを初期化する"""
    if not os.path.exists(CLIENT_SECRETS_FILE):
        create_client_secrets_file()

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=st.secrets.get("REDIRECT_URI", "http://localhost:8501") # Streamlit Cloudでは自動で設定される
    )
    return flow

def login():
    """Google OAuth2認証フローのURLを生成する"""
    flow = get_flow()
    auth_url, _ = flow.authorization_url(prompt='consent')
    st.session_state["auth_url"] = auth_url

def handle_callback():
    """認証コールバックを処理し、ユーザー情報を取得する"""
    if "code" in st.query_params:
        code = st.query_params["code"]
        flow = get_flow()
        flow.fetch_token(code=code)
        creds = flow.credentials

        # ユーザー情報を取得
        oauth2_service = build('oauth2', 'v2', credentials=creds)
        user_info = oauth2_service.userinfo().get().execute()

        st.session_state["user_info"] = user_info
        st.session_state["logged_in"] = True
        st.session_state["creds"] = creds

        # 許可されたメールアドレスかチェック
        authorized_email = st.secrets["AUTHORIZED_USER_EMAIL"]
        if user_info["email"] != authorized_email:
            st.error("このメールアドレスではアクセスが許可されていません。")
            logout()
        else:
            st.success(f"ようこそ、{user_info['name']}さん！")
            # クエリパラメータをクリアしてURLをクリーンにする
            st.query_params.clear()
            st.rerun() # ログイン成功後にページをリロードしてチャットUIを表示

def logout():
    """ログアウト処理"""
    if "logged_in" in st.session_state:
        del st.session_state["logged_in"]
    if "user_info" in st.session_state:
        del st.session_state["user_info"]
    if "creds" in st.session_state:
        del st.session_state["creds"]
    st.info("ログアウトしました。")
    st.rerun()

def check_login():
    """ログイン状態をチェックし、コールバックを処理する"""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # コールバックURLからのリダイレクトを処理
    if "code" in st.query_params and not st.session_state.logged_in:
        handle_callback()

    return st.session_state.logged_in

def get_user_credentials():
    """保存されたユーザー認証情報を取得する"""
    return st.session_state.get("creds")

# アプリケーション起動時に一時ファイルを削除
# Streamlit Cloudではsecrets.tomlから直接読み込むため、このファイルは不要になる
# ローカル開発時のみ必要
if os.path.exists(CLIENT_SECRETS_FILE):
    os.remove(CLIENT_SECRETS_FILE)