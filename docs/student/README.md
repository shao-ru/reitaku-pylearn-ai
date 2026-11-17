# 内容づくり ガイド

このページだけ読めば作業を始められます。設計の詳しい説明（`docs/knowledge_graph.md` など）は、興味があれば後で読んでください。

## 1. やること

**変数とデータ型（var）・入出力（io）・条件分岐（cond）・コレクション（col）** の「知識点」を分担して、AI を使って教材を作ります。

1つの知識点につき、次の2つのファイルを作ります。

| ファイル | 内容 |
| --- | --- |
| 講義ノート | 説明と、実行できるコード例 |
| 練習問題 | 10 問前後（選択問題とコード問題） |

## 2. 覚えておくことは3つだけ

1. **知識点** = 1つのテーマ。`cond_02`（else と elif）のように ID で呼ぶ。
2. **使ってよい文法は、それより前に習う内容だけ。** 知識点ごとの一覧 → [`knowledge_points.md`](knowledge_points.md)
3. **作ったら2つのコマンドで確認する**（§4 の手順 5）。

## 3. 作るファイル

**見本**（cond_02 else と elif）

| 用途 | 講義ノート | 練習問題 |
| --- | --- | --- |
| **AI に渡す・コピーして使う** | `docs/student/examples/cond_02_elseとelif.ipynb` | `docs/student/examples/cond_02_elseとelif_ex01.ipynb` |
| 完成形を見る（ID 付き） | `content/cond/lessons/cond_02_elseとelif.ipynb` | `content/cond/exercises/cond_02_elseとelif_ex01.ipynb` |

`docs/student/examples/` の見本は、問題の見出しが `## 問題` だけ（ID なし）になっています。AI に渡すのは**必ずこちら**にしてください。`content/` の ID 付きのファイルを渡すと、AI が ID までコピーしてしまいます。

**置き場所と名前**

| ファイル | 置き場所と名前 | 例 |
| --- | --- | --- |
| 講義ノート | `content/<トピック>/lessons/<知識点ID>_<タイトル>.ipynb` | `content/var/lessons/var_03_文字列の基本.ipynb` |
| 練習問題 | `content/<トピック>/exercises/<知識点ID>_<タイトル>_ex01.ipynb` | `content/var/exercises/var_03_文字列の基本_ex01.ipynb` |

ファイルの最初のセル（メタデータ）の `id` も、名前に合わせて書き換えます。

- 講義ノート：`id: lesson_var_03`、`knowledge_points: [var_03]`
- 練習問題：`id: var_03_ex01`、`default_knowledge_point: var_03`

## 4. 手順

### 1. 担当を決める

[`knowledge_points.md`](knowledge_points.md) から、メンバーで相談して決めます（`cond_02` は見本なので除く）。

### 2. ブランチを作る

```powershell
git switch main
git pull
git switch -c feature/<名前>-<知識点ID>     # 例：feature/yamada-var03
```

### 3. AI に作ってもらう

AI（Claude、ChatGPT など）に、次の3つを渡します。

- 見本の2ファイル（`docs/student/examples/` の cond_02 講義ノートと練習問題）
- `knowledge_points.md` の「使ってよい文法のルール」と、担当の知識点の行

頼み方の例：

> 添付の見本（cond_02）と同じ形式で、Python 初学者向けの講義ノートと練習問題（ipynb）を作ってください。
> 知識点：var_03「文字列の基本（連結・繰り返し・len）」
> 条件：
> - 添付の「使ってよい文法のルール」を守る（for・while・def・リストなどは使わない）
> - 練習問題は 10 問前後。選択問題を中心に、コード問題（stdio 方式）も入れる
> - 難易度は易しいものから難しいものまで
> - 見本と同じく、メタデータに「下書き」の行、各問題に `タグ: AI作成` を付ける
> - 問題の見出しは `## 問題` だけにする（ID は後でツールが付ける）

### 4. 保存する

§3 の置き場所と名前で保存します。

### 5. コマンドで確認する

```powershell
uv run python -m tools.edu_content assign-ids content/   # 問題に ID を付ける
uv run python -m tools.edu_content validate content/     # 形式をチェックする
```

`エラー 0 件` になれば OK です。エラーが出たら、メッセージを AI に渡して直してもらってかまいません。

**問題の ID について**：ID（`cond_02-3ceba3` のような見出しの後ろの文字列）は自分で書きません。見出しを `## 問題` だけにしておけば、`assign-ids` が自動で付けて ipynb に書き戻します。一度付いた ID は、内容を直しても変えません。

**「ID が重複」というエラーが出たら**：見本などから ID をコピーしてしまった場合です。新しく作った問題の見出しを `## 問題` だけに戻して、`assign-ids` をもう一度実行してください。メタデータの `id`（`cond_02_ex01` など）が重複している場合は、ファイル名に合わせて書き換えます。

### 6. 自分で確認する（大事）

ツールは形式をチェックしますが、内容の正しさは分かりません。次の点を確認してください。

- [ ] **選択問題の正解が正しいか。** 問題のコードを Jupyter（または VS Code）で実際に実行して確かめる。
- [ ] まだ習っていない文法（for・def・リストなど）を使っていないか（`knowledge_points.md` のルール）。
- [ ] 解説が正しく、日本語が自然か。
- [ ] 講義ノートのコード例が、実行してエラーにならないか。

### 7. 提出する

```powershell
git add content/
git commit -m "feat: var_03 の講義ノートと練習問題を追加"
git push -u origin feature/<名前>-<知識点ID>
```

GitHub で Pull Request を作ります。

## 5. 注意

- **他の人の担当ファイルは編集しない。**
- 知識点を増やしたい、名前を変えたいなどと思ったら、`graph.yaml` を直さずに、まず相談する。
- `AI作成` のタグは、自分で直したあとも消さない（どの問題が AI 由来かを研究で使う）。
- 問題やコードに、自分や他人の個人情報（名前・メールアドレスなど）を書かない。

## 6. もっと詳しく知りたいとき

| 知りたいこと | 文書 |
| --- | --- |
| ファイル形式の細かい規則（選択肢の書き方、テストの書き方など） | `docs/content_format.md` §7 |
| 作業手順の詳細、よく出るエラー | `docs/authoring_guide.md` |
| 知識グラフの設計の考え方 | `docs/knowledge_graph.md` |
