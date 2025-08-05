import streamlit as st
from google_auth import check_login, logout, handle_callback, login
from rag_processor import initialize_rag_data, get_conversational_chain
import os

# Streamlitページの基本設定
st.set_page_config(page_title="AI Erika Chat", page_icon="🌸", layout="centered")

# --- Custom CSS for theming --- #
st.markdown("""
<style>
    /* General body styling */
    body {
        background-color: #FFF0F5; /* Lavender Blush - light pink */
        color: #333333;
        font-family: "Shuei MaruGo L", "Shuei NijimiMGo B JIS2004", "ヒラギノ丸ゴ ProN W4", "Hiragino Maru Gothic ProN", "メイリオ", Meiryo, sans-serif !important;
    }
    /* Ensure all h1-h6 tags use the desired font */
    h1, h2, h3, h4, h5, h6 {
        font-family: "Shuei MaruGo L", "Shuei NijimiMGo B JIS2004", "ヒラギノ丸ゴ ProN W4", "Hiragino Maru Gothic ProN", "メイリオ", Meiryo, sans-serif !important;
        color: #333333; /* Dark grey for h1 titles */
    }
    /* Ensure all general text elements use the desired font */
    p, span, div, label, input, textarea, select, button {
        font-family: "Shuei MaruGo L", "Shuei NijimiMGo B JIS2004", "ヒラギノ丸ゴ ProN W4", "Hiragino Maru Gothic ProN", "メイリオ", Meiryo, sans-serif !important;
    }
    /* More specific selector for st.title to ensure black color (if still needed) */
    div[data-testid="stMarkdownContainer"] h1 {
        color: #333333 !important; /* Force dark grey for st.title */
    }
    .stApp {
        background-color: #FFF0F5; /* Lavender Blush */
    }

    /* Header styling */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 20px;
        background-color: #FFC0CB; /* Pink */
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .header-title {
        font-size: 2em;
        font-weight: bold;
        color: #8B008B; /* Dark Magenta */
    }

    /* Chat message styling */
    .stChatMessage {
        padding: 10px 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        max-width: 80%;
        word-wrap: break-word;
    }
    .stChatMessage.st-chat-message-user {
        background-color: #FFDAB9; /* PeachPuff - user bubble */
        align-self: flex-end;
        margin-left: auto; /* Align to right */
        border-bottom-right-radius: 0;
    }
    .stChatMessage.st-chat-message-assistant {
        background-color: #E0FFFF; /* LightCyan - AI bubble */
        align-self: flex-start;
        margin-right: auto; /* Align to left */
        border-bottom-left-radius: 0;
    }

    /* Input form styling */
    .stTextInput > div > div > input {
        border-radius: 20px;
        border: 1px solid #FFB6C1; /* Light Pink */
        padding: 10px 15px;
    }
    .stButton > button {
        background-color: #FF69B4; /* Hot Pink */
        color: white;
        border-radius: 20px;
        padding: 10px 20px;
        border: none;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #FF1493; /* Deep Pink */
    }

    /* Style for st.link_button (Google Login Button) */
    div[data-testid="stLinkButton"] a {
        background-color: #CCCCCC; /* Gray background */
        color: #333333; /* Dark text */
        border-radius: 20px;
        padding: 10px 20px;
        border: none;
        font-weight: bold;
        text-decoration: none; /* Remove underline */
        display: inline-block; /* Make it behave like a block for padding */
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2); /* Add shadow to button */
    }
    div[data-testid="stLinkButton"] a:hover {
        background-color: #AAAAAA; /* Darker gray on hover */
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.3); /* Slightly larger shadow on hover */
    }

    /* Sidebar styling */
    /* Note: These class names can be unstable across Streamlit versions */
    .st-emotion-cache-vk3288 { /* Example class for sidebar background */
        background-color: #FFC0CB; /* Pink */
    }
    .st-emotion-cache-1dp5vir { /* Example class for sidebar header */
        color: #8B008B;
    }

    /* For warning messages text */
    div[data-testid="stAlert"] div[data-testid="stMarkdownContainer"] {
        color: #333333 !important; /* Dark grey for warning text */
    }

    /* Login Box Styling */
    .login-box {
        background-color: white;
        padding: 40px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        text-align: center;
        max-width: 400px;
        margin: 50px auto; /* Center horizontally and add some vertical margin */
    }
    .login-box h1 {
        margin-bottom: 20px;
    }

</style>
""", unsafe_allow_html=True)

# セッションステートの初期化
if "messages" not in st.session_state:
    st.session_state.messages = []
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- 認証フロー --- #
# コールバック処理を先に実行
handle_callback()

if not check_login():
    # ログインしていない場合のUI
    st.markdown("<h1 style='text-align: center; color: #8B008B;'>e-cloud</h1>", unsafe_allow_html=True)

    # ログインボックス
    login_url = st.session_state.get("auth_url")
    if not login_url:
        login() # auth_urlを生成
        st.rerun() # 再度実行してauth_urlを取得

    login_box_html = f"""
    <div class='login-box'>
        <h1 style='text-align: center; color: #333333;'>ログイン</h1>
        <div style='text-align: center; margin-top: 20px;'>
            <a href='{login_url}' style='
                background-color: #CCCCCC; /* Gray background */
                color: #333333; /* Dark text */
                border-radius: 20px;
                padding: 10px 20px;
                border: none;
                font-weight: bold;
                text-decoration: none; /* Remove underline */
                display: inline-block; /* Make it behave like a block for padding */
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2); /* Add shadow to button */
            '>Googleでログイン</a>
        </div>
    </div>
    """
    st.markdown(login_box_html, unsafe_allow_html=True)
    st.stop() # ログインしていない場合はここで処理を停止

# ログイン済みの場合のUI
# ヘッダー
header_cols = st.columns([1, 4, 1])
with header_cols[0]:
    st.markdown("<div class='header-title'>e-cloud</div>", unsafe_allow_html=True)
with header_cols[2]:
    # 設定ボタンとモーダル（st.popoverで簡易的に実現）
    with st.popover("設定"): # 設定ボタン
        st.write("設定項目はまだありません。") # 空の表示

# サイドバーにログアウトボタン
with st.sidebar:
    st.title("AI Erika Chat")
    st.write(f"ようこそ、{st.session_state.user_info['name']}さん！")
    if st.button("ログアウト"): # ログアウトボタンをサイドバーに配置
        logout()

# --- RAGデータの初期化 --- #
# ログイン後に一度だけ実行されるようにする
if "vector_store_initialized" not in st.session_state:
    initialize_rag_data()
    st.session_state.vector_store_initialized = True

# ベクトルストアが利用可能か確認
if "vector_store" not in st.session_state or st.session_state.vector_store is None:
    st.warning("知識データがロードされていないため、RAG機能は利用できません。Google Driveの設定を確認してください。")

# --- チャットUI --- #
# チャットウィンドウ（固定高さでスクロール可能）
chat_container = st.container(height=500, border=True)
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# ユーザー入力の処理
# st.chat_inputは入力フォームと送信ボタンを兼ねる
if prompt := st.chat_input("えりかに話しかけてみよう..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_container: # 新しいメッセージをチャットコンテナに表示
        with st.chat_message("user"):
            st.markdown(prompt)

    with chat_container: # アシスタントの応答をチャットコンテナに表示
        with st.chat_message("assistant"):
            with st.spinner("えりかが考えています..."):
                try:
                    # RAG検索
                    docs = []
                    if st.session_state.vector_store:
                        docs = st.session_state.vector_store.similarity_search(prompt)

                    # 会話チェーンの取得
                    chain = get_conversational_chain()

                    # Gemini APIに問い合わせ
                    assistant_response = chain.invoke({"input_documents": docs, "question": prompt})

                    st.markdown(assistant_response)
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                except Exception as e:
                    error_message = f"ごめんね、エラーが発生しちゃったみたい... ({e})" # 妻の口調を模倣
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})

# アプリケーション起動時に一時ファイルを削除 (google_auth.pyで作成される)
# Streamlit Cloudではsecrets.tomlから直接読み込むため、このファイルは不要になる
# ローカル開発時のみ必要
if os.path.exists("client_secrets.json"):
    os.remove("client_secrets.json")
