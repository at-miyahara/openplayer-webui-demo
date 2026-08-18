# OpenPlayer Web UI — デモ

DMXショープレーヤー **OpenPlayer**（M5Stack CoreS3 + DMX Base）の操作用 Web UI を、
実機なしで触れるようにしたデモです。

**→ https://at-miyahara.github.io/openplayer-webui-demo/**（閲覧には合言葉が必要）

## これは何

実機の Web UI（ファームウェアに埋め込まれて本体から配信されるもの）と同じ HTML を、
そのまま 1 枚のファイルにしたものです。UI 側のコードには手を入れていません。

実機の `/api/*` に相当する応答は、実機から取得したスナップショットを埋め込んで返しています。

- 初期状態の本体に、音楽同調の例としてタイムライン「EDM」を 1 つ入れた構成
- 器具は RGB 50 台 + RGBW 50 台の混在
- 編集した内容はブラウザのメモリ上だけに残ります（リロードで元に戻ります）
- どこにも送信されません。実機も要りません

## 動かない機能

デモに実体を載せていないため、次は動きません。

- バックアップ(.oplay)の作成・復元、音声ファイルの再生
- ファームウェア更新、再起動

## 合言葉について

`index.html` は**入口ページと暗号文だけ**でできています。デモ本体は AES-256-GCM で
暗号化してあり、鍵は合言葉から PBKDF2-SHA256（30 万回）で導きます。復号はブラウザ内で
行われ、合言葉を知らない相手には暗号文しか渡りません。

静的ホスティングなのでサーバー側での認証はできません。「合言葉を入力させるだけ」の画面は
HTML を開けば中身も合言葉も読めてしまうため、中身ごと暗号化する方式にしています。
とはいえ総当たりが不可能なわけではないので、**強く秘匿したいものはここに置かないでください**。

合言葉はこのリポジトリには含まれていません（`tools/passphrase.txt` は `.gitignore` 済み）。

## 更新のしかた

OpenPlayer 本体のリポジトリがこのリポジトリの隣（`../OpenPlayer`）にある前提です。
別の場所なら `OPENPLAYER_ROOT` で指定します。

```sh
./tools/snapshot.sh 10.67.210.1              # 実機から /api/* の控えを取る（USB接続時のIP）
python3 tools/build_demo.py                  # build/demo.plain.html を生成
DEMO_PASSPHRASE='合言葉' node tools/encrypt_page.mjs   # 暗号化して index.html を書き出す
git commit -am "update demo" && git push
```

`tools/passphrase.txt` を置いておけば `DEMO_PASSPHRASE` は省略できます。
合言葉を変えるときは、同じコマンドを新しい合言葉で流し直すだけです。

`webui/index.html`（本体のビルドで生成されるもの）をそのまま取り込むので、
UI 側のコードをこのリポジトリへコピーする必要はありません。

**`build/` を commit しないこと。** 暗号化前の平文がそのまま入っているため、
公開すると暗号化の意味がなくなります（`.gitignore` 済み）。

## ネットワーク情報について

SSID・IPアドレス・ホスト名・製品名はデモ用の値に差し替えてあります。
差し替え表は `tools/build_demo.py` の `SCRUB` にあります。
