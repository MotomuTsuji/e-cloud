import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2 import credentials
import os
import json
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# OAuth2設定
CLIENT_SECRETS_FILE = "client_secrets.json" # 一時ファイルとして作成
SCOPES = ["https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile", "openid"]

def get_redirect_uri():
    """
    環境に応じてリダイレクトURIを返します。
    環境変数 `STREAMLIT_SERVER_ADDRESS` の有無で、
    Streamlit Cloud上かローカルかを判定します。
    """
    # Streamlit Cloud上では `STREAMLIT_SERVER_ADDRESS` が設定される
    if "STREAMLIT_SERVER_ADDRESS" in os.environ:
        return "https://e-cloud.streamlit.app/oauth_callback"
    else:
        # ローカル環境
        return "http://localhost:8501/oauth_callback"

def create_client_secrets_file():
    """Streamlit secretsからクライアントIDとシークレットを読み込み、一時ファイルを作成する"""
    client_id = st.secrets["GOOGLE_CLIENT_ID"]
    client_secret = st.secrets["GOOGLE_CLIENT_SECRET"]

    # Google Cloud Consoleに登録するリダイレクトURIとJS生成元
    # このリストは参考情報であり、実際の認証フローではget_redirect_uri()の値が使われます。
    redirect_uris = ["http://localhost:8501/oauth_callback", "https://e-cloud.streamlit.app/oauth_callback"]
    javascript_origins = ["http://localhost:8501", "https://e-cloud.streamlit.app"]

    client_secrets_data = {
        "web": {
            "client_id": client_id,
            "project_id": "erika-ai-chat", # プロジェクトIDは適宜変更
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": redirect_uris,
            "javascript_origins": javascript_origins
        }
    }
    with open(CLIENT_SECRETS_FILE, "w") as f:
        json.dump(client_secrets_data, f)

def get_flow():
    """OAuth2フローを初期化する"""
    if not os.path.exists(CLIENT_SECRETS_FILE):
        create_client_secrets_file()

    # 現在の環境に応じたリダイレクトURIを取得
    redirect_uri = get_redirect_uri()

    # --- デバッグ情報 ---
    print("--- OAuth Debug Info ---")
    print(f"Redirect URI used: {redirect_uri}")
    client_secrets_data = json.load(open(CLIENT_SECRETS_FILE))
    print(f"Client ID from secrets file: {client_secrets_data['web']['client_id']}")
    print("------------------------")
    # --- デバッグ情報終わり ---

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    return flow

def login():
    """Google OAuth2認証フローのURLを生成する"""
    flow = get_flow()
    auth_url, _ = flow.authorization_url(prompt='consent')
    st.session_state["auth_url"] = auth_url

def handle_callback():
    """認証コールバックを処理し、ユーザー情報を取得する"""
    try:
        code = st.query_params["code"]
        flow = get_flow()
        flow.fetch_token(code=code)
        creds = flow.credentials

        # ユーザー情報を取得
        oauth2_service = build('oauth2', 'v2', credentials=creds)
        user_info = oauth2_service.userinfo().get().execute()

        # 許可されたメールアドレスかチェック
        authorized_email = st.secrets["AUTHORIZED_USER_EMAIL"]
        if user_info["email"] != authorized_email:
            st.error("このメールアドレスではアクセスが許可されていません。")
            logout()
            return

        st.session_state["user_info"] = user_info
        st.session_state["logged_in"] = True
        st.session_state["creds"] = creds

        # 認証完了後、クエリパラメータを削除してトップページにリダイレクト
        st.query_params.clear()
        st.rerun()

    except Exception as e:
        st.error(f"認証中にエラーが発生しました: {e}")
        print(f"Callback error: {e}")
        logout()

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

    # 既存の認証情報を確認し、セッションを復元
    if "creds" in st.session_state and st.session_state.creds:
        creds = st.session_state.creds
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                st.session_state["creds"] = creds # 更新されたクレデンシャルを保存
                print("Google認証情報をリフレッシュしました。")
            except Exception as e:
                print(f"Google認証情報のリフレッシュに失敗しました: {e}")
                logout()
                return False
        
        if not creds.expired:
            try:
                # ユーザー情報を再取得してセッションを確立
                oauth2_service = build('oauth2', 'v2', credentials=creds)
                user_info = oauth2_service.userinfo().get().execute()
                authorized_email = st.secrets["AUTHORIZED_USER_EMAIL"]
                if user_info["email"] == authorized_email:
                    st.session_state["user_info"] = user_info
                    st.session_state["logged_in"] = True
                    print("既存のGoogle認証情報でログイン状態を復元しました。")
                else:
                    st.error("このメールアドレスではアクセスが許可されていません。")
                    logout()
            except Exception as e:
                print(f"既存のGoogle認証情報でのログイン状態復元に失敗しました: {e}")
                logout()

    return st.session_state.logged_in

def get_user_credentials():
    """保存されたユーザー認証情報を取得する"""
    return st.session_state.get("creds")

# アプリケーション起動時に一時ファイルを削除
# Streamlit Cloudではsecrets.tomlから直接読み込むため、このファイルは不要になる
# ローカル開発時のみ必要
if os.path.exists(CLIENT_SECRETS_FILE):
    os.remove(CLIENT_SECRETS_FILE)