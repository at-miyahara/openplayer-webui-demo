#!/usr/bin/env python3
"""OpenPlayer の webui から、実機なしで動くデモ用HTMLを組み立てる。

  ./tools/snapshot.sh <実機のIP>     # 先に /api/* の控えを取る（tools/fixtures/ へ）
  python3 tools/build_demo.py        # build/demo.plain.html を生成
  node tools/encrypt_page.mjs        # 合言葉で暗号化して index.html を書き出す

  ★ build/ の平文は公開リポジトリに入れないこと（入れると暗号化の意味が無くなる）

  - 実機スナップショットを埋め込み、fetch/XHR をシムで受ける（webui 側は無改造）
  - 共有前提なので SSID / IP / MAC由来ホスト名は SCRUB で差し替える
  - mode=artifact だと <html>/<head>/<body> を外した「中身だけ」を吐く
    （claude.ai のアーティファクトは publish 時に外枠を被せるため）
"""
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
# webui の在り処。既定はこのリポジトリの隣に OpenPlayer がある前提
ROOT = Path(os.environ.get('OPENPLAYER_ROOT', REPO.parent / 'OpenPlayer'))
FX = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'fixtures'
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / 'build' / 'demo.plain.html'

TITLE = '新コントローラー WebUIデモ'

# 伏せ字の対応表。ここに置けるのは公開して困らないものだけ。
# ★実機のSSID・IPアドレス・MAC由来のホスト名は「置換元」自体が伏せたい値なので、
#   このリポジトリには置かない。tools/scrub.local.json（.gitignore済み）に
#   {"実際の値": "デモ用の値"} で書くと読み込んで一緒に適用する。
SCRUB = {
    'PICO 2': 'Demo',            # デバイス名。製品名のままだとデモページで浮く
}

_local = HERE / 'scrub.local.json'
if _local.exists():
    SCRUB.update(json.loads(_local.read_text(encoding='utf-8')))
elif FX.exists():
    print('※ tools/scrub.local.json が無い。実機のSSID/IPが控えに残っていないか確認すること')


def scrub(text):
    for a, b in SCRUB.items():
        text = text.replace(a, b)
    return text


def fx_block(name, path):
    """JSON を <script type="application/json"> に載せる。`</script` だけ潰せば安全
    （JSONの文字列内では \\/ は / にデコードされて戻るので中身は変わらない）。"""
    body = scrub(path.read_text(encoding='utf-8')).replace('</script', r'<\/script')
    return f'<script type="application/json" data-fx="{name}">{body}</script>'


def main():
    mode = sys.argv[3] if len(sys.argv) > 3 else 'standalone'
    src = (ROOT / 'webui/index.html').read_text(encoding='utf-8')

    # ヘッダーの製品名だけデモ向けに差し替える。webui 側は無改造で通したいので、
    # ソースではなく生成時に置き換える（h1 は静的HTML＝JSで再描画されない）。
    brand_old = '<h1 class="brand">PICO 2<span'
    assert src.count(brand_old) == 1, 'ヘッダーの構造が変わっている。webui/src/index.html を確認'
    src = src.replace(brand_old, '<h1 class="brand">Demo<span')

    # ヘッダーの「接続: PICO2」も同様。デバイス名由来ではなくアプリ内の直書きで、
    # 静的HTML 2箇所＋タイムラインエディタが書き戻す1箇所（計4つ）にある。
    assert src.count('PICO2') == 4, 'ヘッダーの接続名の箇所数が変わっている。webui を確認'
    src = src.replace('PICO2', 'Demo')

    # webui 内蔵の初期デバイス名。/api/config が返るまでの一瞬だけ見えるので、ここも合わせる。
    dev_old = "deviceName: 'PICO 2'"
    assert src.count(dev_old) == 1, '内蔵の初期デバイス名の書き方が変わっている。webui を確認'
    src = src.replace(dev_old, "deviceName: 'Demo'")

    fixtures = []
    for name, fname in [
        ('status', 'status.json'), ('config', 'config.json'), ('triggers', 'triggers.json'),
        ('audiolist', 'audiolist.json'), ('ntp', 'ntp.json'), ('network', 'network.json'),
        # ショー実体(.SHO バイナリ)と背景画像・音声は載せない。使うのはバックアップ生成だけで、
        # アーティファクトはページ発のダウンロードが効かない＝載せても動かない上に1MB近く太る。
    ]:
        p = FX / fname
        if p.exists():
            fixtures.append(fx_block(name, p))

    shim = (HERE / 'demo_shim.html').read_text(encoding='utf-8')
    payload = '\n'.join(fixtures) + '\n' + shim

    if mode == 'standalone':
        # ★charset の meta より後ろに入れる。前に20KB挟むと、HTTPヘッダの無い file:// で
        #   文字コード判定が先頭1024バイトに届かず化ける。
        anchor = '<meta charset="utf-8">'
        i = src.index(anchor) + len(anchor)
        noindex = ('\n  <!-- デモ用の公開ページ。検索結果には出さない -->'
                   '\n  <meta name="robots" content="noindex, nofollow">')
        out = src[:i] + noindex + '\n' + payload + src[i:]
        out = out.replace('<title>PICO 2 — 操作ツール（試作）</title>',
                          f'<title>{TITLE}</title>')
    else:
        head = src[src.index('<head>') + len('<head>'):src.index('</head>')]
        body_open = re.search(r'<body[^>]*>', src)
        body = src[body_open.end():src.index('</body>')]
        head = re.sub(r'<title>.*?</title>', '', head, flags=re.S)
        out = '\n'.join([f'<title>{TITLE}</title>', payload, head, body])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(out, encoding='utf-8')
    print(f'wrote {OUT} [{mode}] ({len(out.encode("utf-8")):,} bytes)')


main()
