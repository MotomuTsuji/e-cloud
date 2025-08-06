import streamlit as st
import os
import sys

# --- Start of Core Debugging ---
st.set_page_config(layout="wide")
st.error("起動エラーが発生しました。デバッグ情報を表示します。")

st.subheader("Pythonの実行パス")
st.code(sys.executable)

st.subheader("Pythonのバージョン")
st.code(sys.version)

st.subheader("現在の作業ディレクトリ (os.getcwd())")
st.code(os.getcwd())

st.subheader("Pythonパス (sys.path)")
st.code(sys.path)

st.subheader("カレントディレクトリのファイル一覧 (os.listdir('.'))")
try:
    st.code(os.listdir('.'))
except Exception as e:
    st.error(f"カレントディレクトリのファイル一覧を取得できませんでした: {e}")

st.subheader("ソースルートのファイル一覧 (os.listdir('/mount/src/e-cloud'))")
try:
    st.code(os.listdir('/mount/src/e-cloud'))
except Exception as e:
    st.error(f"ソースディレクトリのファイル一覧を取得できませんでした: {e}")

st.subheader("環境変数")
st.write(os.environ)

st.stop() # ここで処理を停止

# --- 元のコード（実行されない） ---
# from google_auth import check_login, logout, handle_callback, login
# from rag_processor import initialize_rag_data, get_conversational_chain