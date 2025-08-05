# AI Erika Chat - セットアップ＆デプロイガイド

これは、Google Gemini APIとRAG（Retrieval-Augmented Generation）技術を用いて、特定の人物（妻・えりか）を模倣するAIチャットアプリケーションです。Google Drive上のファイルを知識ベースとして利用し、Google OAuth2で承認されたユーザーのみが利用できます。

## ✨ 主な機能

-   **AIペルソナチャット:** Gemini APIを利用して、特定の口調や知識を模倣した応答を生成します。
-   **RAGによる知識拡張:** Google Drive上のPDFやテキストファイルを読み込み、AIの応答コンテキストとして活用します。
-   **セキュアな認証:** Google OAuth2を利用し、指定したGoogleアカウントを持つユーザーのみがログインできます。
-   **レスポンシブUI:** Streamlitを使用し、PCとスマートフォンの両方で快適に利用できます。
-   **安全性:** APIキーや認証情報はStreamlit Secretsで安全に管理されます。

## 🚀 セットアップ手順

### ステップ1: Google Cloud Platform (GCP) プロジェクトの設定

1.  **GCPプロジェクトの作成:** 
    *   [Google Cloud Console](https://console.cloud.google.com/)にアクセスし、新しいプロジェクトを作成します（例: `erika-ai-chat`）。

2.  **APIの有効化:** 
    *   作成したプロジェクトで、以下の2つのAPIを有効化します。
        *   **Google Drive API**
        *   **IAM Service Account Credentials API**
    *   ナビゲーションメニューから「APIとサービス」>「ライブラリ」を選択し、各APIを検索して「有効にする」をクリックします。

### ステップ2: 認証情報の作成

#### a. OAuth 2.0 クライアントIDの作成（ユーザー認証用）

1.  「APIとサービス」>「認証情報」に移動します。
2.  「+ 認証情報を作成」>「OAuth クライアント ID」を選択します。
3.  「アプリケーションの種類」で「**ウェブ アプリケーション**」を選択します。
4.  「名前」を入力し（例: `Erika Chat Web Client`）。
5.  「承認済みのリダイレクト URI」に以下を追加します。
    *   **ローカル開発用:** `http://localhost:8501`
    *   **デプロイ後:** Streamlit Cloudでデプロイした後のアプリのURL（例: `https://your-app-name.streamlit.app`）。これはデプロイ後に設定します。
6.  「作成」をクリックすると、**クライアントID**と**クライアントシークレット**が表示されます。これらを安全な場所にコピーしておきます。

#### b. サービスアカウントの作成（Google Driveアクセス用）

1.  「APIとサービス」>「認証情報」に移動します。
2.  「+ 認証情報を作成」>「サービス アカウント」を選択します。
3.  サービスアカウント名を入力し（例: `gdrive-reader`）、「作成して続行」をクリックします。
4.  ロールは不要です。「続行」をクリックし、「完了」します。
5.  作成したサービスアカウントのメールアドレス（`...@...iam.gserviceaccount.com`）をコピーします。
6.  次に、知識ベースとして使用したい**Google Driveのフォルダを、このサービスアカウントのメールアドレスと共有**します（閲覧者権限で十分です）。
7.  サービスアカウントの詳細画面に戻り、「キー」タブを選択します。
8.  「鍵を追加」>「新しい鍵を作成」を選択し、キーのタイプとして「**JSON**」を選び、「作成」をクリックします。
9.  JSONファイルがダウンロードされます。このファイルの内容を後で使います。

### ステップ3: ローカル環境のセットアップ

1.  **リポジトリのクローン:** 
    ```bash
    git clone <your-repository-url>
    cd Erika-Cloud
    ```

2.  **Python仮想環境の作成と有効化:** 
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **必要なライブラリのインストール:** 
    ```bash
    pip install -r requirements.txt
    ```

4.  **Secretsファイルの設定:** 
    *   `.streamlit`ディレクトリを作成し、その中に`secrets.toml`ファイルを作成します。
    *   `secrets.toml`に以下の内容を記述し、自分の情報に書き換えます。

    ```toml
    # .streamlit/secrets.toml

    # Google OAuth2 Client Credentials
    GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
    GOOGLE_CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"

    # User Access Control
    AUTHORIZED_USER_EMAIL = "hoge@gmail.com" # アクセスを許可するあなたのメールアドレス

    # Gemini API Key
    GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

    # Google Drive Folder ID
    # フォルダのURLが https://drive.google.com/drive/folders/ABCDEFG の場合、"ABCDEFG"がID
    GOOGLE_DRIVE_FOLDER_ID = "YOUR_GOOGLE_DRIVE_FOLDER_ID"

    # GCP Service Account Credentials (JSONを一行の文字列にする)
    # ダウンロードしたJSONファイルの中身をコピーし、改行を削除して貼り付けます。
    # 例: '{"type": "service_account", "project_id": "...", ...}'
    GCP_SERVICE_ACCOUNT_CREDS = '{"type": "service_account", "project_id": "...", "private_key_id": "...", "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n", "client_email": "...", "client_id": "...", "auth_uri": "...", "token_uri": "...", "auth_provider_x509_cert_url": "...", "client_x509_cert_url": "..."}'
    ```

### ステップ4: ローカルでの実行

1.  ターミナルで以下のコマンドを実行します。
    ```bash
    streamlit run app.py
    ```
2.  ブラウザで `http://localhost:8501` が開きます。
3.  Googleログインボタンをクリックし、`AUTHORIZED_USER_EMAIL`で指定したアカウントでログインしてください。

## ☁️ Streamlit Cloudへのデプロイ

1.  **GitHubリポジトリの準備:** 
    *   まず、このプロジェクトをGitHubリポジトリとして初期化し、ファイルをコミット・プッシュします。
    *   **注意:** `.streamlit/secrets.toml` は機密情報を含むため、**絶対にGitHubにプッシュしないでください**。`.gitignore` ファイルに `.streamlit/secrets.toml` を追加することを強く推奨します。

    ```bash
    # プロジェクトルートディレクトリで実行
    git init
    git add . # すべてのファイルをステージング
    git rm --cached .streamlit/secrets.toml # secrets.tomlが誤って追加されないようにする
    echo ".streamlit/secrets.toml" >> .gitignore # .gitignoreに追加
    git add .gitignore # .gitignoreもコミット対象に
    git commit -m "Initial commit of AI Erika Chat application"
    git branch -M main
    git remote add origin <あなたのGitHubリポジトリのURL>
    git push -u origin main
    ```
    *   これにより、`app.py`, `google_auth.py`, `rag_processor.py`, `requirements.txt`, `README.md` がGitHubにプッシュされます。

2.  **Streamlit Cloudでのデプロイ:** 
    *   [Streamlit Cloud](https://share.streamlit.io/)にサインアップします。
    *   「New app」をクリックし、デプロイしたいGitHubリポジトリとブランチを選択します。
    *   「Advanced settings...」をクリックします。
    *   「Secrets」セクションに、ローカルの`.streamlit/secrets.toml`ファイルの中身をそのままコピー＆ペーストします。
    *   「Deploy!」をクリックします。

3.  **リダイレクトURIの更新:** 
    *   デプロイが完了すると、アプリのURL（例: `https://erika-ai-chat.streamlit.app`）がわかります。
    *   GCPコンソールの「APIとサービス」>「認証情報」に戻り、ステップ2で作成したOAuthクライアントIDを編集します。
    *   「承認済みのリダイレクト URI」に、この新しいアプリのURLを追加して保存します。

これで、デプロイされたアプリケーションにセキュアにアクセスできるようになります。
