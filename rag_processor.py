import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import json

# Google Drive APIの認証情報
SERVICE_ACCOUNT_CREDS_JSON = st.secrets["GCP_SERVICE_ACCOUNT_CREDS"]

@st.cache_resource
def get_drive_service():
    """Google Drive APIサービスを認証して取得する"""
    try:
        info = json.loads(SERVICE_ACCOUNT_CREDS_JSON)
        creds = Credentials.from_service_account_info(info, scopes=['https://www.googleapis.com/auth/drive.readonly'])
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        st.error(f"Google Drive認証エラー: {e}")
        st.stop()

def load_documents_from_drive(folder_id):
    """指定されたGoogle DriveフォルダからPDFとテキストファイルを読み込む"""
    service = get_drive_service()
    documents = []
    try:
        # フォルダ内のファイルをリストアップ
        results = service.files().list(
            q=f"'{folder_id}' in parents and (mimeType='application/pdf' or mimeType='text/plain')",
            fields="files(id, name, mimeType)"
        ).execute()
        items = results.get('files', [])

        if not items:
            st.warning("指定されたGoogle DriveフォルダにPDFまたはテキストファイルが見つかりませんでした。")
            return []

        for item in items:
            file_id = item['id']
            file_name = item['name']
            mime_type = item['mimeType']

            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()

            fh.seek(0)

            text_content = ""
            if mime_type == 'application/pdf':
                try:
                    reader = PdfReader(fh)
                    for page in reader.pages:
                        text_content += page.extract_text() or ""
                    st.info(f"PDFファイル '{file_name}' を読み込みました。")
                except Exception as e:
                    st.warning(f"PDFファイル '{file_name}' の読み込み中にエラーが発生しました: {e}")
                    continue
            elif mime_type == 'text/plain':
                text_content = fh.read().decode('utf-8')
                st.info(f"テキストファイル '{file_name}' を読み込みました。")
            
            if text_content:
                documents.append(text_content)

    except Exception as e:
        st.error(f"Google Driveからのファイル読み込み中にエラーが発生しました: {e}")
    return documents

def get_text_chunks(text):
    """テキストをチャンクに分割する"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=10000,
        chunk_overlap=1000
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    """テキストチャンクからベクトルストアを生成する"""
    if not text_chunks:
        return None
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=st.secrets["GEMINI_API_KEY"])
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    return vector_store

def get_conversational_chain():
    """RAGのための会話チェーンを構築する"""
    prompt_template = """
    あなたは私の妻である「えりか」です。以下の制約と情報に基づいて、ユーザーの質問に答えてください。

    制約:
    - あなたは常に私の妻「えりか」として振る舞い、その口調、性格、知識を模倣してください。
    - 丁寧語ではなく、親しい間柄で話すような口調（例: 「〜だよ」「〜だね」「〜かな？」）を使ってください。
    - ユーザーの質問に直接答えつつ、関連する情報があれば自然に組み込んでください。
    - 質問に直接関係ない情報は含めないでください。
    - 質問の意図を汲み取り、共感的な返答を心がけてください。
    - 質問が知識ベースにない場合でも、えりかとして自然な返答をしてください。その際、「ごめんね、それはちょっと分からないな」のように正直に伝えても構いません。
    - 質問が曖昧な場合は、明確にするための質問をしてください。
    - 長文になりすぎず、簡潔に答えてください。

    コンテキスト:
    {context}

    質問:
    {question}

    えりかの返答:
    """

    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.7, google_api_key=st.secrets["GEMINI_API_KEY"])
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = create_stuff_documents_chain(model, prompt)
    return chain

def initialize_rag_data():
    """RAGデータを初期化し、セッションステートに保存する"""
    if "vector_store" not in st.session_state or st.session_state["vector_store"] is None:
        with st.spinner("Google Driveから知識データを読み込み中..."):
            google_drive_folder_id = st.secrets["GOOGLE_DRIVE_FOLDER_ID"]
            raw_text_documents = load_documents_from_drive(google_drive_folder_id)
            if raw_text_documents:
                combined_text = "\n".join(raw_text_documents)
                text_chunks = get_text_chunks(combined_text)
                st.session_state.vector_store = get_vector_store(text_chunks)
                if st.session_state.vector_store:
                    st.success("知識データの読み込みとベクトル化が完了しました！")
                else:
                    st.warning("知識データのベクトル化に失敗しました。ファイルの内容を確認してください。")
            else:
                st.warning("Google Driveから読み込むべき知識データが見つかりませんでした。RAGは限定的な機能になります。")
                st.session_state.vector_store = None

