// 生成済みのデモHTMLを合言葉で暗号化し、入口ページ(index.html)を書き出す。
//
//   DEMO_PASSPHRASE=... node tools/encrypt_page.mjs
//   （環境変数が無ければ tools/passphrase.txt を読む。どちらも公開リポジトリには入れない）
//
// 静的ホスティングなのでサーバー側で認証はできない。代わりに中身ごと暗号化して、
// 合言葉を知っている人のブラウザだけが復号できるようにする＝URLが漏れても暗号文しか渡らない。
// 「合言葉を入力させるだけ」の画面は、HTMLを開けば中身も合言葉も読めるので意味がない。
import { createHash, pbkdf2Sync, randomBytes, createCipheriv } from 'node:crypto';
import { gzipSync } from 'node:zlib';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = dirname(HERE);
const ITERATIONS = 300_000;

const pass = (process.env.DEMO_PASSPHRASE
  || (existsSync(join(HERE, 'passphrase.txt')) ? readFileSync(join(HERE, 'passphrase.txt'), 'utf8') : '')).trim();
if (!pass) {
  console.error('合言葉がない。DEMO_PASSPHRASE を渡すか tools/passphrase.txt を置くこと。');
  process.exit(1);
}

const plainPath = join(REPO, 'build', 'demo.plain.html');
const plain = readFileSync(plainPath);
const packed = gzipSync(plain, { level: 9 });

const salt = randomBytes(16);
const iv = randomBytes(12);
const key = pbkdf2Sync(pass, salt, ITERATIONS, 32, 'sha256');
const cipher = createCipheriv('aes-256-gcm', key, iv);
// WebCrypto の decrypt は「暗号文＋認証タグ」を1つの塊として受け取るので、連結して渡す
const body = Buffer.concat([cipher.update(packed), cipher.final(), cipher.getAuthTag()]);

const gate = readFileSync(join(HERE, 'gate.html'), 'utf8')
  .replace('__SALT__', salt.toString('base64'))
  .replace('__IV__', iv.toString('base64'))
  .replace('__ITER__', String(ITERATIONS))
  .replace('__PAYLOAD__', body.toString('base64'));

const out = join(REPO, 'index.html');
writeFileSync(out, gate);

const kb = n => (n / 1024).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + ' KB';
console.log(`plain   ${kb(plain.length)}`);
console.log(`gzip    ${kb(packed.length)}`);
console.log(`index   ${kb(Buffer.byteLength(gate))}  (sha256 ${createHash('sha256').update(gate).digest('hex').slice(0, 12)})`);
