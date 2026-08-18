# 生成ツール

デモページ（リポジトリ直下の `index.html`）を組み立てる一式。

## 更新

OpenPlayer 本体のリポジトリが隣（`../OpenPlayer`）にある前提。別の場所なら `OPENPLAYER_ROOT` で指定する。

```sh
./tools/snapshot.sh 10.67.210.1     # 実機から /api/* の控えを取る
python3 tools/build_demo.py         # build/demo.plain.html を生成
node tools/encrypt_page.mjs         # 暗号化して index.html を書き出す
```

合言葉は `tools/passphrase.txt`、または `DEMO_PASSPHRASE` で渡す。変えるときは新しい合言葉で流し直すだけ。

本体の `webui/index.html`（ビルド生成物）をそのまま取り込むので、UI のコードをこちらへコピーする必要はない。
UI 側は無改造で、製品名などの差し替えは生成時に当てている。出現数を `assert` しているので、
本体の文言が変わればビルドが止まる。

## コミットしてはいけないもの

いずれも `.gitignore` 済み。公開リポジトリなので、入った時点で意味が失われる。

| | |
|---|---|
| `build/` | 暗号化前の平文。公開すると `index.html` の暗号化が無意味になる |
| `tools/fixtures/` | 実機の控え。SSID・IP が生のまま入っている |
| `tools/scrub.local.json` | 伏せ字の対応表。**置換元が伏せたい値そのもの** |
| `tools/passphrase.txt` | 合言葉 |

## 仕組み

`index.html` は入口ページと暗号文だけ。デモ本体は gzip して AES-256-GCM で暗号化してあり、
鍵は合言葉から PBKDF2-SHA256（30 万回）で導く。復号はブラウザ内で行う。

静的ホスティングではサーバー側で認証できない。合言葉を照合するだけの画面は HTML を開けば
中身も合言葉も読めるので、中身ごと暗号化している。総当たりが不可能なわけではないため、
**強く秘匿したいものは置かない**こと。

実機の `/api/*` は `demo_shim.html` が `fetch` と XHR を横取りして控えを返す。POST の内容は
セッション中だけ保持するので、編集して保存し直す動作まで通る。
